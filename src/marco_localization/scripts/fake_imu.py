#!/usr/bin/env python3
"""Sahte IMU yayinicisi — donanim baglanana kadar EKF imu:=true testi icin.

/imu/data_raw topigine sensor_msgs/Imu yazar (frame_id=imu_link).
ivme: yercekimi (z=+g), gyro: sifir (hareketsiz). Gercek IMU gelince
bu dugum yerine donanim surucusu kullanilir.

  ros2 run marco_localization fake_imu.py
  ros2 launch marco_localization localization.launch.py sahte:=true imu:=true
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu


class FakeImu(Node):
    """Sabit yercekimi + sifir gyro yayinlar."""

    def __init__(self) -> None:
        super().__init__("fake_imu")
        self.declare_parameter("rate_hz", 50.0)
        self.declare_parameter("frame_id", "imu_link")
        rate = float(self.get_parameter("rate_hz").value)
        self._frame = str(self.get_parameter("frame_id").value)
        self._pub = self.create_publisher(Imu, "/imu/data_raw", 10)
        self.create_timer(1.0 / rate, self._tick)
        self.get_logger().info(
            f"fake_imu hazir | {rate:.0f} Hz | frame={self._frame} | "
            "/imu/data_raw (yercekimi, gyro=0)"
        )

    def _tick(self) -> None:
        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self._frame
        # Yercekimi +z (ENU/URDF: z yukari). Madgwick gravity removal icin.
        msg.linear_acceleration.x = 0.0
        msg.linear_acceleration.y = 0.0
        msg.linear_acceleration.z = 9.80665
        msg.angular_velocity.x = 0.0
        msg.angular_velocity.y = 0.0
        msg.angular_velocity.z = 0.0
        # Kovaryans: diyagonal; -1 = bilinmiyor kullanma, sifir = guven.
        msg.linear_acceleration_covariance[0] = 0.01
        msg.linear_acceleration_covariance[4] = 0.01
        msg.linear_acceleration_covariance[8] = 0.01
        msg.angular_velocity_covariance[0] = 0.001
        msg.angular_velocity_covariance[4] = 0.001
        msg.angular_velocity_covariance[8] = 0.001
        msg.orientation_covariance[0] = -1.0
        self._pub.publish(msg)


def main() -> None:
    rclpy.init()
    dugum = FakeImu()
    try:
        rclpy.spin(dugum)
    except KeyboardInterrupt:
        pass
    finally:
        dugum.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
