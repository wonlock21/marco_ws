#!/usr/bin/env python3
"""Headless/visible Phase 8 acceptance against real ROS and Fortress processes."""

import json
import math
import os
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from ros_gz_interfaces.msg import Entity
from ros_gz_interfaces.srv import DeleteEntity, SpawnEntity
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, String
from std_srvs.srv import SetBool
from tf2_msgs.msg import TFMessage


def percentile(values, fraction):
    if not values:
        return None
    values = sorted(values)
    index = (len(values) - 1) * fraction
    low = int(index)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (index - low)


class Acceptance(Node):
    """Exercise obstacle, mux and fail-safe behavior without Phase 6/7 reruns."""

    def __init__(self):
        super().__init__('phase8_acceptance')
        self.declare_parameter('result_path', '/tmp/marco_phase8/headless.json')
        self.declare_parameter('fault_scenario', '')
        self.raw_pub = self.create_publisher(Twist, '/cmd_vel_raw', 10)
        self.manual_pub = self.create_publisher(Twist, '/cmd_vel_manual', 10)
        self.dock_pub = self.create_publisher(Twist, '/cmd_vel_dock', 10)
        self.estop_pub = self.create_publisher(Bool, '/base/estop', 10)
        self.mode_pub = self.create_publisher(Bool, '/base/manual_mode', 10)
        self.cmd = Twist()
        self.safe = Twist()
        self.odom = None
        self.state = {}
        self.samples = []
        self.safe_samples = []
        self.odom_samples = []
        self.times = {name: [] for name in ('scan', 'odom', 'tf', 'cmd_vel')}
        self.create_subscription(Twist, '/cmd_vel', self._cmd_cb, 30)
        self.create_subscription(Twist, '/cmd_vel_safe', self._safe_cb, 30)
        self.create_subscription(Odometry, '/odom', self._odom_cb, 30)
        self.create_subscription(LaserScan, '/scan',
                                 lambda _: self.times['scan'].append(time.monotonic()), 10)
        self.create_subscription(TFMessage, '/tf',
                                 lambda _: self.times['tf'].append(time.monotonic()), 30)
        self.create_subscription(String, '/safety/state', self._state_cb, 10)
        self.spawn = self.create_client(SpawnEntity, '/world/marco_test/create')
        self.remove = self.create_client(DeleteEntity, '/world/marco_test/remove')
        self.scan_gate = self.create_client(
            SetBool, '/simulation_scan_gate/set_enabled')

    def _cmd_cb(self, msg):
        self.cmd = msg
        self.samples.append((time.monotonic(), msg.linear.x, msg.angular.z))
        self.times['cmd_vel'].append(time.monotonic())

    def _safe_cb(self, msg):
        self.safe = msg
        self.safe_samples.append((time.monotonic(), msg.linear.x))

    def _odom_cb(self, msg):
        self.odom = msg
        p = msg.pose.pose.position
        self.odom_samples.append((time.monotonic(), p.x, p.y))
        self.times['odom'].append(time.monotonic())

    def _state_cb(self, msg):
        try:
            self.state = json.loads(msg.data)
        except json.JSONDecodeError:
            pass

    def spin_until(self, predicate, timeout, publish=None):
        end = time.monotonic() + timeout
        while rclpy.ok() and time.monotonic() < end:
            if publish:
                publish()
            rclpy.spin_once(self, timeout_sec=0.04)
            if predicate():
                return True
        return False

    @staticmethod
    def twist(linear=0.0, angular=0.0):
        msg = Twist()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)
        return msg

    def publish_inputs(self, raw=None, manual=None, dock=None,
                       estop=False, manual_mode=False):
        if raw is not None:
            self.raw_pub.publish(self.twist(raw))
        if manual is not None:
            self.manual_pub.publish(self.twist(manual))
        if dock is not None:
            self.dock_pub.publish(self.twist(dock))
        self.estop_pub.publish(Bool(data=estop))
        self.mode_pub.publish(Bool(data=manual_mode))

    def pose(self):
        p = self.odom.pose.pose
        q = p.orientation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y),
                         1 - 2 * (q.y * q.y + q.z * q.z))
        return p.position.x, p.position.y, yaw

    def obstacle(self, name, longitudinal):
        if not self.spawn.wait_for_service(timeout_sec=5):
            return False
        x, y, yaw = self.pose()
        request = SpawnEntity.Request()
        request.entity_factory.name = name
        request.entity_factory.sdf = (
            "<sdf version='1.7'><model name='%s'><static>true</static><link name='link'>"
            "<collision name='c'><geometry><box><size>0.16 0.70 0.80</size></box>"
            "</geometry></collision><visual name='v'><geometry><box><size>0.16 0.70 0.80"
            "</size></box></geometry><material><ambient>1 0 0 1</ambient><diffuse>1 0 0 1"
            "</diffuse></material></visual></link></model></sdf>" % name)
        request.entity_factory.pose.position.x = x + longitudinal * math.cos(yaw)
        request.entity_factory.pose.position.y = y + longitudinal * math.sin(yaw)
        request.entity_factory.pose.position.z = 0.4
        request.entity_factory.pose.orientation.w = 1.0
        future = self.spawn.call_async(request)
        return self.spin_until(future.done, 8) and future.result().success

    def delete(self, name):
        request = DeleteEntity.Request()
        request.entity.name = name
        request.entity.type = Entity.MODEL
        future = self.remove.call_async(request)
        return self.spin_until(future.done, 8) and future.result().success

    def stage_obstacle(self, label, command, position, expected_speed):
        def publish():
            self.publish_inputs(raw=command)
        self.spin_until(lambda: abs(self.cmd.linear.x) > 0.05, 3, publish)
        before = self.pose()[:2]
        start = time.monotonic()
        sample_start = len(self.samples)
        spawned = self.obstacle(label, position)
        triggered = self.spin_until(
            lambda: bool(self.state.get('obstacle')) if expected_speed == 0.0
            else bool(self.state.get('slowdown')), 4, publish)
        trigger_time = time.monotonic()
        stopped = self.spin_until(
            lambda: (len(self.samples) > sample_start and
                     self.samples[-1][0] >= trigger_time and
                     abs(self.cmd.linear.x) <= expected_speed + 0.015), 4, publish)
        stop_time = time.monotonic()
        at_stop = self.pose()[:2]
        observed = [abs(v) for t, v, _ in self.samples
                    if trigger_time <= t <= stop_time]
        removed = self.delete(label) if spawned else False
        resumed = self.spin_until(lambda: abs(self.cmd.linear.x) > 0.05, 4, publish)
        resume_time = time.monotonic()
        return {
            'spawned': spawned, 'triggered': triggered, 'removed': removed,
            'stopped_or_slowed': stopped,
            'trigger_sec': trigger_time - start,
            'stop_sec': stop_time - trigger_time,
            'stop_distance_m': math.hypot(at_stop[0] - before[0], at_stop[1] - before[1]),
            'observed_speed_mps': min(observed) if observed else None,
            'continued_same_command': resumed,
            'resume_sec': resume_time - stop_time,
        }

    def mux_test(self):
        result = {}
        cases = [
            ('nav', dict(raw=0.11), 0.11),
            ('manual_over_nav', dict(raw=0.11, manual=0.22), 0.22),
            ('dock_over_manual', dict(raw=0.11, manual=0.22, dock=0.33), 0.33),
            ('manual_mode_blocks_nav', dict(raw=0.11, manual_mode=True), 0.0),
            ('manual_mode_manual', dict(raw=0.11, manual=0.22, manual_mode=True), 0.22),
            ('manual_mode_dock', dict(raw=0.11, dock=0.33, manual_mode=True), 0.33),
        ]
        for name, args, expected in cases:
            ok = self.spin_until(lambda: abs(self.cmd.linear.x - expected) < 0.025,
                                 2, lambda a=args: self.publish_inputs(**a))
            result[name] = {'passed': ok, 'expected': expected,
                            'observed': self.cmd.linear.x}
            self.spin_until(lambda: False, 0.7,
                            lambda: self.publish_inputs(raw=0.0))
        return result

    def hz(self, key):
        values = self.times[key]
        return ((len(values) - 1) / (values[-1] - values[0])
                if len(values) > 1 and values[-1] > values[0] else None)

    def run(self):
        ready = self.spin_until(
            lambda: self.odom is not None and len(self.times['scan']) > 5 and self.state,
            30, lambda: self.publish_inputs(raw=0.0))
        if self.get_parameter('fault_scenario').value == 'tf_loss':
            passed = self.spin_until(
                lambda: ('tf_missing_or_stale' in self.state.get('reason', [])
                         and abs(self.cmd.linear.x) < 1e-4),
                3, lambda: self.publish_inputs(raw=0.25))
            result = {
                'passed': passed, 'scenario': 'tf_loss',
                'tf_missing_or_stale_zero': passed,
                'state': self.state,
                'final_twist': {'linear_x': self.cmd.linear.x,
                                'angular_z': self.cmd.angular.z},
            }
            path = str(self.get_parameter('result_path').value)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as stream:
                json.dump(result, stream, indent=2, sort_keys=True)
            return passed
        if self.get_parameter('fault_scenario').value == 'obstacle_timeout':
            spawned = self.obstacle('phase8_timeout_obstacle', 0.72)
            passed = self.spin_until(
                lambda: ('obstacle_wait_timeout' in
                         self.state.get('reason', []) and
                         abs(self.cmd.linear.x) < 1e-4),
                12, lambda: self.publish_inputs(raw=0.25))
            removed = self.delete('phase8_timeout_obstacle') if spawned else False
            result = {
                'passed': bool(spawned and passed and removed),
                'scenario': 'obstacle_timeout', 'spawned': spawned,
                'timeout_zero': passed, 'removed': removed,
                'configured_timeout_s': self.state.get(
                    'obstacle_wait_timeout_s'),
                'final_twist': {'linear_x': self.cmd.linear.x,
                                'angular_z': self.cmd.angular.z},
            }
            path = str(self.get_parameter('result_path').value)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as stream:
                json.dump(result, stream, indent=2, sort_keys=True)
            return result['passed']
        forward_slow = self.stage_obstacle('phase8_forward_slow', 0.40, 1.15, 0.10)
        forward_stop = self.stage_obstacle('phase8_forward_stop', 0.40, 0.72, 0.0)
        reverse_slow = self.stage_obstacle('phase8_reverse_slow', -0.30, -1.68, 0.075)
        reverse_stop = self.stage_obstacle('phase8_reverse_stop', -0.30, -1.30, 0.0)

        estop_start = time.monotonic()
        self.spin_until(lambda: abs(self.cmd.linear.x) > 0.05, 2,
                        lambda: self.publish_inputs(raw=0.25))
        asserted = time.monotonic()
        estop_zero = self.spin_until(
            lambda: abs(self.cmd.linear.x) < 1e-4, 2,
            lambda: self.publish_inputs(raw=0.25, estop=True))
        estop_stop = time.monotonic()
        no_restart = not self.spin_until(
            lambda: abs(self.cmd.linear.x) > 0.02, 1,
            lambda: self.publish_inputs(raw=0.0, estop=False))
        restarted = self.spin_until(
            lambda: abs(self.cmd.linear.x) > 0.05, 2,
            lambda: self.publish_inputs(raw=0.25, estop=False))
        estop = {'zero_observed': estop_zero, 'stop_sec': estop_stop - asserted,
                 'no_self_restart': no_restart, 'new_command_restart': restarted,
                 'duration_sec': time.monotonic() - estop_start}

        mux = self.mux_test()
        input_loss = self.spin_until(
            lambda: abs(self.cmd.linear.x) < 1e-4 and self.state.get('guard_zero'),
            2)
        scan_loss = False
        scan_restored = False
        if self.scan_gate.wait_for_service(timeout_sec=3):
            request = SetBool.Request(data=False)
            future = self.scan_gate.call_async(request)
            self.spin_until(future.done, 2)
            scan_loss = self.spin_until(
                lambda: 'scan_timeout' in self.state.get('reason', []) and
                abs(self.cmd.linear.x) < 1e-4, 2,
                lambda: self.publish_inputs(raw=0.25))
            request = SetBool.Request(data=True)
            future = self.scan_gate.call_async(request)
            self.spin_until(future.done, 2)
            scan_restored = self.spin_until(
                lambda: bool(self.state.get('scan_fresh')), 2,
                lambda: self.publish_inputs(raw=0.0))

        self.spin_until(lambda: abs(self.cmd.linear.x) < 1e-4, 2,
                        lambda: self.publish_inputs(raw=0.0))
        ownership = {topic: [item.node_name for item in
                             self.get_publishers_info_by_topic(topic)]
                     for topic in ('/cmd_vel_raw', '/cmd_vel_safe', '/cmd_vel')}
        all_stages = [forward_slow, forward_stop, reverse_slow, reverse_stop]
        passed = (ready and all(item['spawned'] and item['triggered'] and
                                item['stopped_or_slowed'] and item['removed'] and
                                item['continued_same_command'] for item in all_stages)
                  and all(item['passed'] for item in mux.values())
                  and all((estop_zero, no_restart, restarted, input_loss,
                           scan_loss, scan_restored))
                  and abs(self.cmd.linear.x) < 1e-4)
        result = {
            'passed': passed, 'ready': ready,
            'forward': {'slow': forward_slow, 'stop': forward_stop},
            'reverse': {'slow': reverse_slow, 'stop': reverse_stop},
            'estop': estop, 'mux': mux,
            'negative': {'input_timeout_zero': input_loss,
                         'scan_timeout_zero': scan_loss,
                         'scan_restored': scan_restored},
            'ownership': ownership,
            'topic_hz': {key: self.hz(key) for key in self.times},
            'tf_drop': 0 if self.times['tf'] else 1,
            'cross_track_p95_m': percentile(
                [abs(y) for _, _, y in self.odom_samples], 0.95),
            'cross_track_max_m': max(
                [abs(y) for _, _, y in self.odom_samples], default=None),
            'final_twist': {'linear_x': self.cmd.linear.x,
                            'angular_z': self.cmd.angular.z},
        }
        path = str(self.get_parameter('result_path').value)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
        self.get_logger().info('PHASE8_RESULT=%s %s' %
                               ('PASS' if passed else 'FAIL', path))
        return passed


def main():
    rclpy.init()
    node = Acceptance()
    try:
        success = node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()
    raise SystemExit(0 if success else 1)


if __name__ == '__main__':
    main()
