#!/usr/bin/env python3
"""Send a deterministic simulation goal sequence through NavigateToPose."""

import json
import math
import os
import time

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node


GOALS = [('forward', 2.0, 0.0, 0.0), ('turning', 5.0, 3.5, 0.52),
         ('reverse', 4.17, 3.0, 0.52), ('return', 0.0, 0.0, 0.52)]


class GoalRunner(Node):
    def __init__(self):
        super().__init__('nav2_test_goals')
        self.declare_parameter('scenario', 'nominal')
        self.declare_parameter('timeout', 600.0)
        self.declare_parameter('result_path', '/tmp/marco_phase6/goals.json')
        self.client = ActionClient(self, NavigateToPose, '/navigate_to_pose')
        self.stop = self.create_publisher(Twist, '/cmd_vel', 10)
        self.results = []

    def zero(self):
        for _ in range(5):
            self.stop.publish(Twist()); rclpy.spin_once(self, timeout_sec=0.03)

    def run(self):
        deadline = time.monotonic() + self.get_parameter('timeout').value
        if not self.client.wait_for_server(timeout_sec=120.0):
            raise RuntimeError('navigate_to_pose action is not ready')
        for name, x, y, yaw in GOALS:
            goal = NavigateToPose.Goal(); goal.behavior_tree = ''
            goal.pose = PoseStamped(); goal.pose.header.frame_id = 'map'
            goal.pose.header.stamp = self.get_clock().now().to_msg()
            goal.pose.pose.position.x = float(x); goal.pose.pose.position.y = float(y)
            goal.pose.pose.orientation.z = math.sin(yaw / 2); goal.pose.pose.orientation.w = math.cos(yaw / 2)
            started = time.monotonic(); future = self.client.send_goal_async(goal)
            rclpy.spin_until_future_complete(self, future, timeout_sec=10.0)
            handle = future.result()
            if handle is None or not handle.accepted:
                self.results.append({'name': name, 'status': 'REJECTED'}); break
            result = handle.get_result_async()
            while rclpy.ok() and not result.done() and time.monotonic() < deadline:
                rclpy.spin_once(self, timeout_sec=0.1)
            if not result.done():
                handle.cancel_goal_async(); self.results.append({'name': name, 'status': 'TIMEOUT'}); break
            code = result.result().status
            self.results.append({'name': name, 'status': 'SUCCEEDED' if code == GoalStatus.STATUS_SUCCEEDED else str(code),
                                 'duration_sec': time.monotonic() - started})
            self.zero()
            if code != GoalStatus.STATUS_SUCCEEDED: break
        self.zero()
        path = self.get_parameter('result_path').value + '.goals'
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as stream: json.dump(self.results, stream, indent=2)


def main(args=None):
    rclpy.init(args=args); node = GoalRunner()
    try: node.run()
    except (KeyboardInterrupt, Exception) as exc:
        node.get_logger().error(str(exc)); node.zero()
    finally:
        node.zero(); node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()


if __name__ == '__main__': main()
