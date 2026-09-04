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
from std_srvs.srv import Trigger
from tf2_ros import Buffer, TransformException, TransformListener


ZERO_EPS = 1.0e-4


class SafetySupervisor(Node):
    """Publish measured obstacle/fault state and force an explicit zero on faults."""

    def __init__(self, **kwargs):
        super().__init__('safety_supervisor', **kwargs)
        self.declare_parameter('base_frame', 'base_footprint')
        self.declare_parameter('scan_timeout_s', 0.5)
        self.declare_parameter('tf_timeout_s', 0.5)
        self.declare_parameter('input_timeout_s', 0.5)
        self.declare_parameter('base_communication_timeout_s', 0.75)
        self.declare_parameter('require_base_communication', True)
        # Zero disables automatic cancellation. Production policy is to hold a
        # safe zero for as long as the obstacle exists and resume only after it
        # clears; a positive value is retained solely for explicit test profiles.
        self.declare_parameter('obstacle_wait_timeout_s', 0.0)
        self.declare_parameter('stop_min_points', 2)
        self.declare_parameter('slow_min_points', 3)
        self.declare_parameter('obstacle_detection_enabled', True)
        self._base = str(self.get_parameter('base_frame').value)
        self._scan_timeout = float(self.get_parameter('scan_timeout_s').value)
        self._tf_timeout = float(self.get_parameter('tf_timeout_s').value)
        self._input_timeout = float(self.get_parameter('input_timeout_s').value)
        self._base_communication_timeout = float(
            self.get_parameter('base_communication_timeout_s').value)
        if self._base_communication_timeout <= 0.0:
            raise ValueError(
                'base_communication_timeout_s sifirdan buyuk olmali')
        self._require_base_communication = bool(
            self.get_parameter('require_base_communication').value)
        self._wait_timeout = float(
            self.get_parameter('obstacle_wait_timeout_s').value)
        if self._wait_timeout < 0.0:
            raise ValueError('obstacle_wait_timeout_s sifir veya pozitif olmali')
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
        self._base_communication_ok = False
        self._base_communication_wall = None
        self._last_inputs = {'nav': None, 'manual': None, 'dock': None}
        self._last_input_moving = {'nav': False, 'manual': False, 'dock': False}
        self._operator_reset_required = False
        self._stop_since = None
        self._obstacle_timed_out = False
        self._cancel_sent = False
        self._current_reasons = []
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
            Bool, '/base/communication_ok', self._on_base_communication, 10)
        self.create_subscription(
            Twist, '/cmd_vel_safe', lambda msg: self._on_input('nav', msg), 10)
        self.create_subscription(
            Twist, '/cmd_vel_manual', lambda msg: self._on_input('manual', msg), 10)
        self.create_subscription(
            Twist, '/cmd_vel_dock', lambda msg: self._on_input('dock', msg), 10)
        self.create_service(Trigger, '/safety/reset', self._on_reset)

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
        self._last_inputs[name] = time.monotonic()
        self._last_input_moving[name] = self._moving(msg)

    def _on_estop(self, msg):
        active = bool(msg.data)
        if active and not self._estop:
            self._operator_reset_required = True
            self._cancel_navigation()
            self._abort_pub.publish(Bool(data=True))
        self._estop = active

    def _fresh_moving_inputs(self, now):
        return [
            name for name, stamp in self._last_inputs.items()
            if stamp is not None
            and now - stamp <= self._input_timeout
            and self._last_input_moving[name]
        ]

    def _on_reset(self, _request, response):
        """Clear the post-E-stop latch only after an explicit, safe reset."""
        now = time.monotonic()
        if self._estop:
            response.success = False
            response.message = 'e-stop halen aktif'
            return response
        moving = self._fresh_moving_inputs(now)
        if moving:
            response.success = False
            response.message = 'hareket komutu aktif: ' + ','.join(moving)
            return response
        blocking = [
            reason for reason in self._current_reasons
            if reason not in (
                'operator_reset_required', 'nav_input_timeout',
                'manual_input_timeout', 'dock_input_timeout')
        ]
        if blocking:
            response.success = False
            response.message = 'guvenlik arizasi aktif: ' + ','.join(blocking)
            return response
        self._operator_reset_required = False
        self._abort_pub.publish(Bool(data=False))
        response.success = True
        response.message = 'operator safety reset kabul edildi'
        return response

    def _on_manual_mode(self, msg):
        self._manual_mode = bool(msg.data)

    def _on_base_communication(self, msg):
        self._base_communication_ok = bool(msg.data)
        self._base_communication_wall = time.monotonic()

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
        if self._operator_reset_required:
            reasons.append('operator_reset_required')
        base_communication_fresh = (
            self._base_communication_wall is not None
            and now - self._base_communication_wall
            <= self._base_communication_timeout)
        if self._require_base_communication:
            if not base_communication_fresh:
                reasons.append('base_communication_timeout')
            elif not self._base_communication_ok:
                reasons.append('base_communication_lost')

        input_fresh, selected = self._selected_input_fresh(now)
        if not input_fresh:
            reasons.append(selected + '_input_timeout')

        if stop:
            if self._stop_since is None:
                self._stop_since = now
            # Collision Monitor protects the Nav2 branch. This independent,
            # highest-priority guard also blocks manual and docking commands.
            reasons.append('obstacle')
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

        self._current_reasons = list(reasons)
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
            'base_communication_required': self._require_base_communication,
            'base_communication_fresh': base_communication_fresh,
            'base_communication_ok': self._base_communication_ok,
            'operator_reset_required': self._operator_reset_required,
            'waiting_for_obstacle_clear': stop,
            'obstacle_wait_s': (
                max(0.0, now - self._stop_since)
                if self._stop_since is not None else 0.0),
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
