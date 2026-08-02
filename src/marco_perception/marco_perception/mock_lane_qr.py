#!/usr/bin/env python3
"""Sahte serit + QR yayinicisi (goruntu ekibi gelene kadar).

Topikler (PROJE_PLANI sozlesmesi):
  /lane/offset   marco_msgs/LaneOffset
  /qr/detection  marco_msgs/QrDetection

Senaryo (parametre):
  success      — hatalar zamanla 0'a iner (docking smoke)
  qr_mismatch  — QR istasyon_id ile uyusmaz
  lane_lost    — bir sure sonra serit kaybolur

  ros2 run marco_perception mock_lane_qr.py
  ros2 launch marco_perception mock_perception.launch.py
"""

from __future__ import annotations

import math

import rclpy
from rclpy.node import Node

from marco_msgs.msg import LaneOffset, QrDetection


class MockLaneQr(Node):
    """Serit/QR mock — docking kapali cevrimini besler."""

    def __init__(self) -> None:
        super().__init__("mock_lane_qr")
        self.declare_parameter("rate_hz", 20.0)
        self.declare_parameter("scenario", "success")
        self.declare_parameter("station_id", "istasyon_A")
        self.declare_parameter("wrong_station_id", "istasyon_YANLIS")
        self.declare_parameter("camera_frame", "camera_front_optical_frame")
        self.declare_parameter("initial_lateral_m", 0.12)
        self.declare_parameter("initial_heading_rad", 0.15)
        self.declare_parameter("decay_tau_s", 4.0)

        rate = float(self.get_parameter("rate_hz").value)
        self._scenario = str(self.get_parameter("scenario").value)
        self._station = str(self.get_parameter("station_id").value)
        self._wrong = str(self.get_parameter("wrong_station_id").value)
        self._camera = str(self.get_parameter("camera_frame").value)
        self._lat0 = float(self.get_parameter("initial_lateral_m").value)
        self._yaw0 = float(self.get_parameter("initial_heading_rad").value)
        self._tau = max(0.5, float(self.get_parameter("decay_tau_s").value))

        self._lane_pub = self.create_publisher(LaneOffset, "/lane/offset", 10)
        self._qr_pub = self.create_publisher(QrDetection, "/qr/detection", 10)
        self._t0 = self.get_clock().now()
        self.create_timer(1.0 / rate, self._tick)
        self.get_logger().info(
            f"mock_lane_qr | {rate:.0f} Hz | scenario={self._scenario} | "
            f"station={self._station}"
        )

    def _elapsed(self) -> float:
        return (self.get_clock().now() - self._t0).nanoseconds * 1e-9

    def _tick(self) -> None:
        t = self._elapsed()
        stamp = self.get_clock().now().to_msg()

        qr = QrDetection()
        qr.header.stamp = stamp
        qr.header.frame_id = self._camera
        qr.detected = True
        qr.confidence = 0.95
        qr.camera_frame = self._camera
        if self._scenario == "qr_mismatch":
            qr.data = self._wrong
        else:
            qr.data = self._station
        qr.pose_in_camera.x = 1.2
        qr.pose_in_camera.y = 0.0
        qr.pose_in_camera.theta = 0.0
        self._qr_pub.publish(qr)

        lane = LaneOffset()
        lane.header.stamp = stamp
        lane.header.frame_id = self._camera
        lane.camera_frame = self._camera

        if self._scenario == "lane_lost" and t > 2.0:
            lane.detected = False
            lane.confidence = 0.0
            lane.lateral_offset = 0.0
            lane.heading_error = 0.0
        else:
            # success / qr_mismatch: hatalar exponential decay
            decay = math.exp(-t / self._tau)
            lane.detected = True
            lane.confidence = 0.9
            lane.lateral_offset = self._lat0 * decay
            lane.heading_error = self._yaw0 * decay
        self._lane_pub.publish(lane)


def main() -> None:
    rclpy.init()
    node = MockLaneQr()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
