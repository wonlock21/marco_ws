#!/usr/bin/env python3
"""Hedef ve olculen diferansiyel teker hizlarini terminale yazar."""

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node


class WheelTerminalMonitor(Node):
    def __init__(self):
        super().__init__('wheel_terminal_monitor')
        self.declare_parameter('wheel_separation', 0.460)
        self.wheel_separation = float(
            self.get_parameter('wheel_separation').value)
        self.target = (0.0, 0.0)
        self.measured = (0.0, 0.0)
        self.create_subscription(Twist, '/cmd_vel', self._on_cmd, 10)
        self.create_subscription(Odometry, '/odom', self._on_odom, 10)
        self.create_timer(0.5, self._print_values)

    def _wheel_speeds(self, linear, angular):
        half_track = self.wheel_separation * 0.5
        return (
            (linear - angular * half_track) * 1000.0,
            (linear + angular * half_track) * 1000.0,
        )

    def _on_cmd(self, msg):
        self.target = self._wheel_speeds(msg.linear.x, msg.angular.z)

    def _on_odom(self, msg):
        twist = msg.twist.twist
        self.measured = self._wheel_speeds(
            twist.linear.x, twist.angular.z)

    def _print_values(self):
        target_left, target_right = self.target
        measured_left, measured_right = self.measured
        self.get_logger().info(
            f'[TEKER] hedef sol={target_left:+.0f} '
            f'sag={target_right:+.0f} mm/s | '
            f'olculen sol={measured_left:+.0f} '
            f'sag={measured_right:+.0f} mm/s')


def main():
    rclpy.init()
    node = WheelTerminalMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
