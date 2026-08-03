#!/usr/bin/env python3
"""Repeatable AMCL route with straight, left/right and 0.50 rad/s turns."""

import math
import time
import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_msgs.msg import Bool, String


def yaw(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y*q.y + q.z*q.z))


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


class Drive(Node):
    def __init__(self):
        super().__init__('amcl_test_drive')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.done = self.create_publisher(Bool, '/amcl_test/completed', 1)
        self.stage_pub = self.create_publisher(String, '/amcl_test/stage', 10)
        self.create_subscription(Odometry, '/ground_truth/odom', self.odom_cb, 20)
        self.create_subscription(PoseWithCovarianceStamped, '/amcl_pose', self.amcl_cb, 10)
        self.pose = None
        self.have_amcl = False
        self.started = time.monotonic()
        self.stage_started = None
        # Known-free loop returning to the map/world origin.
        self.goals = [(0.0, -2.7), (2.2, -2.7), (2.2, -0.4),
                      (0.0, -0.4), (-1.3, -0.4), (-1.3, -2.7),
                      (0.0, -2.7), (0.0, 0.0)]
        self.index = 0
        self.finished = False
        self.timer = self.create_timer(0.05, self.tick)

    def odom_cb(self, msg): self.pose = msg.pose.pose
    def amcl_cb(self, _msg): self.have_amcl = True

    def command(self, v=0.0, w=0.0):
        msg = Twist(); msg.linear.x = v; msg.angular.z = w; self.pub.publish(msg)

    def stop(self):
        for _ in range(10): self.command()

    def finish(self, ok, reason=''):
        if self.finished: return
        self.finished = True; self.stop(); self.done.publish(Bool(data=ok))
        (self.get_logger().info if ok else self.get_logger().error)(reason or 'AMCL route complete')

    def tick(self):
        if self.finished: self.command(); return
        # Motion is needed for AMCL to publish after an initial pose; do not
        # deadlock waiting for a second static /amcl_pose sample.
        if self.pose is None:
            self.command()
            if time.monotonic() - self.started > 60: self.finish(False, 'startup timeout')
            return
        now = self.get_clock().now()
        if self.stage_started is None: self.stage_started = now
        if (now - self.stage_started).nanoseconds > 60_000_000_000:
            self.finish(False, 'waypoint timeout'); return
        p = self.pose.position; heading = yaw(self.pose.orientation)
        gx, gy = self.goals[self.index]; dx, dy = gx-p.x, gy-p.y
        dist = math.hypot(dx, dy)
        if dist < 0.18:
            self.command(); self.index += 1; self.stage_started = now
            if self.index == len(self.goals): self.finish(True); return
            self.stage_pub.publish(String(data='waypoint_%d' % self.index)); return
        error = wrap(math.atan2(dy, dx) - heading)
        if abs(error) > 0.18:
            # Explicitly exercise both turn signs and the required 0.50 rad/s section.
            self.command(0.0, math.copysign(0.50, error)); return
        self.command(min(0.28, max(0.10, 0.45 * dist)), max(-0.35, min(0.35, 1.2*error)))

    def destroy_node(self):
        if rclpy.ok(): self.stop()
        return super().destroy_node()


def main(args=None):
    rclpy.init(args=args); node = Drive()
    try: rclpy.spin(node)
    except (KeyboardInterrupt, Exception) as exc:
        if not isinstance(exc, KeyboardInterrupt): node.get_logger().error(str(exc))
    finally:
        node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()


if __name__ == '__main__': main()
