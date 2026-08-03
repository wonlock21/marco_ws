#!/usr/bin/env python3
"""Reliably deliver a bounded, covariance-bearing AMCL initial pose."""

import math
import time

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.duration import Duration
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy
from std_msgs.msg import Bool


class InitialPose(Node):
    def __init__(self):
        super().__init__('amcl_initial_pose')
        for name, default in [('initial_x', 0.0), ('initial_y', 0.0),
                              ('initial_yaw', 0.0), ('timeout', 35.0)]:
            self.declare_parameter(name, default)
        qos = QoSProfile(depth=1, reliability=QoSReliabilityPolicy.RELIABLE,
                         durability=QoSDurabilityPolicy.VOLATILE)
        self.pub = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', qos)
        event_qos = QoSProfile(depth=1, reliability=QoSReliabilityPolicy.RELIABLE,
                               durability=QoSDurabilityPolicy.TRANSIENT_LOCAL)
        self.event_pub = self.create_publisher(Bool, '/amcl_test/initial_pose_sent', event_qos)
        self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.pose_cb, 10)
        self.started = time.monotonic()
        self.sent = 0
        self.have_pose = False
        self.timer = self.create_timer(0.5, self.tick)

    def pose_cb(self, _msg):
        if self.sent:
            self.have_pose = True

    def tick(self):
        if self.have_pose or time.monotonic() - self.started > self.get_parameter('timeout').value:
            return
        if self.pub.get_subscription_count() < 1 or self.sent >= 8:
            return
        msg = PoseWithCovarianceStamped()
        msg.header.frame_id = 'map'
        msg.header.stamp = (self.get_clock().now()-Duration(seconds=0.25)).to_msg()
        msg.pose.pose.position.x = float(self.get_parameter('initial_x').value)
        msg.pose.pose.position.y = float(self.get_parameter('initial_y').value)
        yaw = float(self.get_parameter('initial_yaw').value)
        msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        msg.pose.pose.orientation.w = math.cos(yaw / 2.0)
        msg.pose.covariance[0] = 0.05 ** 2
        msg.pose.covariance[7] = 0.05 ** 2
        msg.pose.covariance[35] = math.radians(3.0) ** 2
        self.pub.publish(msg)
        self.event_pub.publish(Bool(data=True))
        self.sent += 1
        self.get_logger().info('Initial pose %d/8 delivered (subscriber ready).' % self.sent)


def main(args=None):
    rclpy.init(args=args)
    node = InitialPose()
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
