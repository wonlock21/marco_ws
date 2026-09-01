#!/usr/bin/env python3
"""Observable fail-safe state and zero-velocity guard for Phase 8."""

import json
import math
import time

import rclpy
from action_msgs.srv import CancelGoal
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, String
from tf2_ros import Buffer, TransformException, TransformListener


ZERO_EPS = 1.0e-4


class SafetySupervisor(Node):
    """Publish measured obstacle/fault state and force an explicit zero on faults."""

    def __init__(self):
        super().__init__('safety_supervisor')
        self.declare_parameter('base_frame', 'base_footprint')
        self.declare_parameter('scan_timeout_s', 0.5)
        self.declare_parameter('tf_timeout_s', 0.5)
        self.declare_parameter('input_timeout_s', 0.5)
        self.declare_parameter('obstacle_wait_timeout_s', 15.0)
        self.declare_parameter('stop_min_points', 2)
        self.declare_parameter('slow_min_points', 3)
        self.declare_parameter('obstacle_detection_enabled', True)
        self._base = str(self.get_parameter('base_frame').value)
        self._scan_timeout = float(self.get_parameter('scan_timeout_s').value)
        self._tf_timeout = float(self.get_parameter('tf_timeout_s').value)
        self._input_timeout = float(self.get_parameter('input_timeout_s').value)
        self._wait_timeout = float(
            self.get_parameter('obstacle_wait_timeout_s').value)
        self._stop_n = int(self.get_parameter('stop_min_points').value)
        self._slow_n = int(self.get_parameter('slow_min_points').value)
        self._obstacle_detection_enabled = bool(
            self.get_parameter('obstacle_detection_enabled').value)

        self._tf = Buffer()
        self._listener = TransformListener(self._tf, self)
        self._scan_wall = None
        self._scan_stamp = None
        self._scan_frame = ''
        self._points = []
        self._estop = False
        self._manual_mode = False
        self._last_inputs = {'nav': None, 'manual': None, 'dock': None}
        self._post_estop_command_required = False
        self._estop_clear_wall = 0.0
        self._stop_since = None
        self._obstacle_timed_out = False
        self._cancel_sent = False
        self._last_reason = ''

        self._guard_pub = self.create_publisher(Twist, '/cmd_vel_safety_guard', 10)
        self._obstacle_pub = self.create_publisher(
            Bool, '/safety/obstacle_detected', 10)
        self._state_pub = self.create_publisher(String, '/safety/state', 10)
        self._abort_pub = self.create_publisher(Bool, '/safety/navigation_abort', 10)
        self.create_subscription(
            LaserScan, 'scan', self._on_scan, qos_profile_sensor_data)
        self.create_subscription(Bool, '/base/estop', self._on_estop, 10)
        self.create_subscription(Bool, '/base/manual_mode', self._on_manual_mode, 10)
        self.create_subscription(
            Twist, '/cmd_vel_safe', lambda msg: self._on_input('nav', msg), 10)
        self.create_subscription(
            Twist, '/cmd_vel_manual', lambda msg: self._on_input('manual', msg), 10)
        self.create_subscription(
            Twist, '/cmd_vel_dock', lambda msg: self._on_input('dock', msg), 10)

        self._cancel_clients = [self.create_client(
            CancelGoal, name + '/_action/cancel_goal') for name in (
                '/navigate_to_pose', '/navigate_through_poses', '/follow_path',
                '/compute_and_track_route', '/spin')]
        self.create_timer(0.05, self._tick)

    @staticmethod
    def _moving(msg):
        return (abs(msg.linear.x) > ZERO_EPS or abs(msg.linear.y) > ZERO_EPS or
                abs(msg.angular.z) > ZERO_EPS)

    def _on_input(self, name, msg):
        now = time.monotonic()
        self._last_inputs[name] = now
        if (self._post_estop_command_required and now > self._estop_clear_wall and
                self._moving(msg)):
            self._post_estop_command_required = False

    def _on_estop(self, msg):
        active = bool(msg.data)
        if self._estop and not active:
            self._post_estop_command_required = True
            self._estop_clear_wall = time.monotonic()
        self._estop = active

    def _on_manual_mode(self, msg):
        self._manual_mode = bool(msg.data)

    def _on_scan(self, msg):
        now = time.monotonic()
        self._scan_wall = now
        self._scan_stamp = msg.header.stamp
        self._scan_frame = msg.header.frame_id
        points = []
        angle = msg.angle_min
        for distance in msg.ranges:
            if math.isfinite(distance) and msg.range_min <= distance <= msg.range_max:
                points.append((distance * math.cos(angle), distance * math.sin(angle)))
            angle += msg.angle_increment
        self._points = points

    def _base_points(self):
        transform = self._tf.lookup_transform(
            self._base, self._scan_frame, rclpy.time.Time())
        q = transform.transform.rotation
        yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                         1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        c, s = math.cos(yaw), math.sin(yaw)
        tx = transform.transform.translation.x
        ty = transform.transform.translation.y
        return [(tx + c * x - s * y, ty + s * x + c * y)
                for x, y in self._points], transform

    @staticmethod
    def _count(points, xmin, xmax, ymax):
        return sum(xmin <= x <= xmax and abs(y) <= ymax for x, y in points)

    def _selected_input_fresh(self, now):
        # Dock has highest motion priority. Manual mode blocks nav but not dock/manual.
        dock = self._last_inputs['dock']
        manual = self._last_inputs['manual']
        nav = self._last_inputs['nav']

        def fresh(stamp):
            return stamp is not None and now - stamp <= self._input_timeout

        if fresh(dock):
            return True, 'dock'
        if self._manual_mode:
            return fresh(manual), 'manual'
        if fresh(manual):
            return True, 'manual'
        return fresh(nav), 'nav'

    def _cancel_navigation(self):
        request = CancelGoal.Request()  # zero UUID + zero stamp means cancel all goals
        for client in self._cancel_clients:
            if client.service_is_ready():
                client.call_async(request)

    def _tick(self):
        now = time.monotonic()
        reasons = []
        scan_fresh = self._scan_wall is not None and now - self._scan_wall <= self._scan_timeout
        stop = slow = tf_fresh = False
        direction = 'none'
        if scan_fresh and self._scan_frame:
            try:
                points, transform = self._base_points()
                stamp = transform.header.stamp
                tf_age = self.get_clock().now().nanoseconds / 1e9 - (
                    stamp.sec + stamp.nanosec / 1e9)
                # Static transforms conventionally have stamp zero and do not expire.
                tf_fresh = (stamp.sec == 0 and stamp.nanosec == 0) or tf_age <= self._tf_timeout
                front_stop = self._count(points, 0.0, 0.85, 0.45) >= self._stop_n
                rear_stop = self._count(points, -1.40, 0.0, 0.45) >= self._stop_n
                front_slow = self._count(points, 0.0, 1.30, 0.60) >= self._slow_n
                rear_slow = self._count(points, -1.85, 0.0, 0.60) >= self._slow_n
                if self._obstacle_detection_enabled:
                    stop = front_stop or rear_stop
                    slow = front_slow or rear_slow
                    direction = ('both' if front_stop and rear_stop else
                                 'front' if front_stop else
                                 'rear' if rear_stop else 'none')
            except TransformException:
                tf_fresh = False
        if not scan_fresh:
            reasons.append('scan_timeout')
        if not tf_fresh:
            reasons.append('tf_missing_or_stale')
        if self._estop:
            reasons.append('estop')
        if self._post_estop_command_required:
            reasons.append('new_command_required')

        input_fresh, selected = self._selected_input_fresh(now)
        if not input_fresh:
            reasons.append(selected + '_input_timeout')

        if stop:
            if self._stop_since is None:
                self._stop_since = now
            if self._wait_timeout > 0.0 and now - self._stop_since >= self._wait_timeout:
                self._obstacle_timed_out = True
                reasons.append('obstacle_wait_timeout')
        else:
            self._stop_since = None
            self._obstacle_timed_out = False
            self._cancel_sent = False
        if self._obstacle_timed_out and not self._cancel_sent:
            self._cancel_navigation()
            self._abort_pub.publish(Bool(data=True))
            self._cancel_sent = True

        guard = bool(reasons)
        if guard:
            self._guard_pub.publish(Twist())
        self._obstacle_pub.publish(Bool(data=stop))
        state = {
            'obstacle': stop, 'slowdown': slow, 'direction': direction,
            'obstacle_detection_enabled': self._obstacle_detection_enabled,
            'scan_fresh': scan_fresh, 'tf_fresh': tf_fresh,
            'selected_input': selected, 'input_fresh': input_fresh,
            'estop': self._estop, 'guard_zero': guard,
            'reason': reasons, 'obstacle_wait_timeout_s': self._wait_timeout,
        }
        self._state_pub.publish(String(data=json.dumps(state, sort_keys=True)))
        reason = ','.join(reasons)
        if reason != self._last_reason:
            self.get_logger().info('guard=%s reason=%s' % (guard, reason or 'none'))
            self._last_reason = reason


def main():
    rclpy.init()
    node = SafetySupervisor()
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
