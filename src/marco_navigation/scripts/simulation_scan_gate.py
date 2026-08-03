#!/usr/bin/env python3
"""Simulation-only LaserScan gate for deterministic Nav2 fault acceptance."""

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_srvs.srv import SetBool


class ScanGate(Node):
    def __init__(self):
        super().__init__('simulation_scan_gate')
        self.enabled = True
        self.publisher = self.create_publisher(LaserScan, '/scan_nav2', qos_profile_sensor_data)
        self.create_subscription(LaserScan, '/scan', self.scan_cb, qos_profile_sensor_data)
        self.create_service(SetBool, '~/set_enabled', self.set_enabled)

    def scan_cb(self, msg):
        if self.enabled:
            self.publisher.publish(msg)

    def set_enabled(self, request, response):
        self.enabled = request.data
        response.success = True
        response.message = 'enabled' if self.enabled else 'disabled'
        return response


def main(args=None):
    rclpy.init(args=args)
    node = ScanGate()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
