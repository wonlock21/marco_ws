#!/usr/bin/env python3
"""Simulation-only LaneOffset/QrDetection source from Gazebo ground truth."""

import math

import rclpy
from marco_msgs.msg import LaneOffset, QrDetection
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from tf2_msgs.msg import TFMessage


class Phase9SimInputs(Node):
    """Publish idealized contract messages; never use this node on hardware."""

    def __init__(self):
        super().__init__('phase9_sim_inputs')
        self.declare_parameter('rate_hz', 20.0)
        self.declare_parameter('station_id', 'istasyon_A')
        self.declare_parameter('camera_frame', 'camera_front_optical_frame')
        self.declare_parameter('target_stop_distance_m', 0.75)
        self.declare_parameter('lane_fault_mode', '')
        self.declare_parameter('qr_fault_mode', '')
        self._pose = None
        self._lane_pub = self.create_publisher(LaneOffset, '/lane/offset', 10)
        self._qr_pub = self.create_publisher(QrDetection, '/qr/detection', 10)
        self.create_subscription(
            TFMessage, '/world/marco_test/dynamic_pose/info', self._on_pose,
            qos_profile_sensor_data)
        rate = max(1.0, float(self.get_parameter('rate_hz').value))
        self.create_timer(1.0 / rate, self._publish)
        self.get_logger().warning(
            'SIMULATION/TEST ONLY: LaneOffset and QrDetection come from Gazebo ground truth')

    def _on_pose(self, msg):
        for transform in msg.transforms:
            if transform.child_frame_id == 'marco':
                p = transform.transform.translation
                q = transform.transform.rotation
                yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                                 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
                if all(math.isfinite(v) for v in (p.x, p.y, yaw)):
                    self._pose = (p.x, p.y, yaw)

    def _publish(self):
        if self._pose is None:
            return
        x, y, yaw = self._pose
        now = self.get_clock().now().to_msg()
        frame = str(self.get_parameter('camera_frame').value)
        lane_fault = str(self.get_parameter('lane_fault_mode').value)
        qr_fault = str(self.get_parameter('qr_fault_mode').value)

        if lane_fault != 'stale':
            lane = LaneOffset()
            lane.header.stamp, lane.header.frame_id = now, frame
            lane.camera_frame = ('wrong_camera' if lane_fault == 'wrong_camera' else frame)
            lane.detected = lane_fault not in ('lost', 'camera_lost')
            lane.confidence = 0.05 if lane_fault == 'low_confidence' else 1.0
            lane.lateral_offset = -y
            lane.heading_error = -yaw
            self._lane_pub.publish(lane)

        if qr_fault != 'stale':
            qr = QrDetection()
            qr.header.stamp, qr.header.frame_id = now, frame
            qr.camera_frame = ('wrong_camera' if qr_fault == 'wrong_camera' else frame)
            qr.detected = qr_fault not in ('lost', 'camera_lost')
            qr.confidence = 0.05 if qr_fault == 'low_confidence' else 1.0
            qr.data = ('istasyon_YANLIS' if qr_fault == 'mismatch' else
                       str(self.get_parameter('station_id').value))
            target = float(self.get_parameter('target_stop_distance_m').value)
            qr.pose_in_camera.x = target - x
            qr.pose_in_camera.y = -y
            qr.pose_in_camera.theta = -yaw
            self._qr_pub.publish(qr)


def main():
    rclpy.init()
    node = Phase9SimInputs()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
