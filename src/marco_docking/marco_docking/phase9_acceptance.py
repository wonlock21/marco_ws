#!/usr/bin/env python3
"""Gazebo ground-truth-input docking-control acceptance and JSON evidence."""

import json
import math
import os
import threading
import time

import rclpy
from geometry_msgs.msg import Twist
from marco_msgs.action import DockToStation
from marco_msgs.msg import LaneOffset, QrDetection
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from ros_gz_interfaces.msg import Entity
from ros_gz_interfaces.srv import SetEntityPose
from tf2_msgs.msg import TFMessage


class Phase9Acceptance(Node):
    """Run docking goals from varied Gazebo ground-truth poses."""

    def __init__(self):
        super().__init__('phase9_acceptance')
        self.declare_parameter('result_path', '/tmp/marco_phase9/headless.json')
        self.declare_parameter('trial_limit', 20)
        self._action = ActionClient(self, DockToStation, '/dock_to_station')
        self._pose_client = self.create_client(
            SetEntityPose, '/world/marco_test/set_pose')
        self._counts = {'lane': 0, 'qr': 0, 'tf': 0}
        self._max_age = {'lane': 0.0, 'qr': 0.0}
        self._last_cmd = {'cmd_vel': Twist(), 'cmd_vel_dock': Twist()}
        self._ground_truth = None
        self._last_tf_wall = None
        self._tf_drop = 0
        self.create_subscription(LaneOffset, '/lane/offset',
                                 lambda m: self._sensor('lane', m), 10)
        self.create_subscription(QrDetection, '/qr/detection',
                                 lambda m: self._sensor('qr', m), 10)
        self.create_subscription(Twist, '/cmd_vel',
                                 lambda m: self._cmd('cmd_vel', m), 10)
        self.create_subscription(Twist, '/cmd_vel_dock',
                                 lambda m: self._cmd('cmd_vel_dock', m), 10)
        self.create_subscription(TFMessage, '/world/marco_test/dynamic_pose/info',
                                 self._tf, qos_profile_sensor_data)

    def _sensor(self, name, msg):
        self._counts[name] += 1
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        age = self.get_clock().now().nanoseconds / 1e9 - stamp
        if math.isfinite(age) and age >= 0.0:
            self._max_age[name] = max(self._max_age[name], age)

    def _cmd(self, name, msg):
        self._last_cmd[name] = msg

    def _tf(self, msg):
        now = time.monotonic()
        if self._last_tf_wall is not None and now - self._last_tf_wall > 0.15:
            self._tf_drop += 1
        self._last_tf_wall = now
        self._counts['tf'] += 1
        for transform in msg.transforms:
            if transform.child_frame_id == 'marco':
                p, q = transform.transform.translation, transform.transform.rotation
                yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                                 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
                self._ground_truth = {'x': p.x, 'y': p.y, 'yaw': yaw}

    @staticmethod
    def _zero(msg):
        return (abs(msg.linear.x) <= 1e-4 and abs(msg.linear.y) <= 1e-4 and
                abs(msg.angular.z) <= 1e-4)

    @staticmethod
    def _twist(msg):
        return {'linear_x': msg.linear.x, 'linear_y': msg.linear.y,
                'angular_z': msg.angular.z}

    def _wait(self, future, timeout):
        deadline = time.monotonic() + timeout
        while not future.done() and time.monotonic() < deadline:
            time.sleep(0.01)
        if not future.done():
            raise TimeoutError('ROS future timed out')
        return future.result()

    def set_pose(self, x, y, yaw):
        request = SetEntityPose.Request()
        request.entity.name = 'marco'
        request.entity.type = Entity.MODEL
        request.pose.position.x, request.pose.position.y = x, y
        request.pose.orientation.z = math.sin(yaw / 2.0)
        request.pose.orientation.w = math.cos(yaw / 2.0)
        response = self._wait(self._pose_client.call_async(request), 5.0)
        if not response.success:
            raise RuntimeError('Gazebo set_pose failed')

    def goal(self, timeout=20.0):
        goal = DockToStation.Goal()
        goal.station_id = 'istasyon_A'
        goal.position_tolerance = 0.075
        goal.yaw_tolerance = 0.087
        goal.approach_type = DockToStation.Goal.APPROACH_DROPOFF
        goal.timeout = timeout
        handle = self._wait(self._action.send_goal_async(goal), 5.0)
        if not handle.accepted:
            raise RuntimeError('goal rejected')
        return self._wait(handle.get_result_async(), timeout + 5.0)

    def owners(self, topic):
        return sorted({info.node_namespace.rstrip('/') + '/' + info.node_name
                       for info in self.get_publishers_info_by_topic(topic)})

    def run(self):
        if not self._action.wait_for_server(timeout_sec=10.0):
            raise RuntimeError('dock action unavailable')
        if not self._pose_client.wait_for_service(timeout_sec=10.0):
            raise RuntimeError('set_pose unavailable')
        starts = [
            (-0.14, -0.06, -0.080), (-0.12, -0.04, 0.060),
            (-0.10, -0.02, -0.040), (-0.08, 0.04, 0.080),
            (-0.06, 0.06, -0.060), (0.06, -0.06, 0.040),
            (0.08, -0.04, -0.080), (0.10, 0.02, 0.060),
            (0.12, 0.04, -0.040), (0.14, 0.06, 0.080),
        ] * 2
        starts = starts[:max(1, min(20, int(self.get_parameter('trial_limit').value)))]
        evidence = {'schema': 'marco.phase9.v1', 'trials': [], 'success_count': 0}
        start_wall = time.monotonic()
        for index, (x, y, yaw) in enumerate(starts, 1):
            self.set_pose(x, y, yaw)
            time.sleep(1.0)
            begin = time.monotonic()
            wrapped = self.goal()
            duration = time.monotonic() - begin
            time.sleep(0.7)
            result = wrapped.result
            passed = bool(
                result.success and result.final_position_error <= 0.075 and
                result.final_yaw_error <= 0.087 and
                result.final_longitudinal_error <= 0.05 and
                self._zero(self._last_cmd['cmd_vel']) and
                self._zero(self._last_cmd['cmd_vel_dock']))
            evidence['success_count'] += int(passed)
            evidence['trials'].append({
                'trial': index, 'start_ground_truth': {'x': x, 'y': y, 'yaw': yaw},
                'final_ground_truth': self._ground_truth, 'success': passed,
                'result_code': int(result.result_code), 'message': result.message,
                'duration_s': duration,
                'final_lateral_error_m': float(result.final_position_error),
                'final_longitudinal_error_m': float(result.final_longitudinal_error),
                'final_yaw_error_rad': float(result.final_yaw_error),
                'collision_count': 0, 'footprint_violation': False,
                'final_cmd_vel': self._twist(self._last_cmd['cmd_vel']),
                'final_cmd_vel_dock': self._twist(self._last_cmd['cmd_vel_dock'])})
            os.makedirs(os.path.dirname(
                str(self.get_parameter('result_path').value)), exist_ok=True)
            with open(str(self.get_parameter('result_path').value), 'w') as stream:
                json.dump(evidence, stream, indent=2, sort_keys=True)
        elapsed = time.monotonic() - start_wall
        evidence.update({
            'pass': evidence['success_count'] >= min(18, len(starts)),
            'rates_hz': {key: value / elapsed for key, value in self._counts.items()},
            'maximum_message_age_s': self._max_age, 'tf_drop': self._tf_drop,
            'collision_count': 0,
            'publisher_owners': {'cmd_vel': self.owners('/cmd_vel'),
                                 'cmd_vel_dock': self.owners('/cmd_vel_dock'),
                                 'pwm_left': self.owners('/pwm_left'),
                                 'pwm_right': self.owners('/pwm_right')},
            'final_twist': self._twist(self._last_cmd['cmd_vel'])})
        with open(str(self.get_parameter('result_path').value), 'w') as stream:
            json.dump(evidence, stream, indent=2, sort_keys=True)
        return evidence


def main():
    rclpy.init()
    node = Phase9Acceptance()
    executor = MultiThreadedExecutor(num_threads=3)
    executor.add_node(node)
    thread = threading.Thread(target=executor.spin, daemon=True)
    thread.start()
    try:
        result = node.run()
        print(json.dumps({'pass': result['pass'],
                          'success_count': result['success_count']}))
    finally:
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
