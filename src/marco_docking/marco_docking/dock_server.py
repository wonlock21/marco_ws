#!/usr/bin/env python3
"""Fail-safe camera lane/QR DockToStation action server."""

import math
import threading
import time

import rclpy
from geometry_msgs.msg import Twist
from marco_msgs.action import DockToStation
from marco_msgs.msg import LaneOffset, QrDetection
from nav_msgs.msg import Odometry
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import Bool, String


def reverse_lane_command(lane, angular_sign, max_linear, max_angular):
    """Convert a forward lane command to bounded rear-camera reverse motion."""
    values = (lane.linear.x, lane.angular.z, angular_sign)
    if not all(math.isfinite(float(value)) for value in values):
        raise ValueError('non-finite lane command')
    cmd = Twist()
    cmd.linear.x = -min(abs(float(lane.linear.x)), abs(float(max_linear)))
    cmd.angular.z = max(
        -abs(float(max_angular)),
        min(
            abs(float(max_angular)),
            float(angular_sign) * float(lane.angular.z),
        ),
    )
    return cmd


class DockServer(Node):
    """Drive through cmd_vel_dock and verify terminal errors."""

    def __init__(self):
        super().__init__('dock_server')
        defaults = {
            'control_rate_hz': 20.0, 'max_linear_vel': 0.05,
            'max_angular_vel': 0.40, 'kp_lateral': 1.2,
            'kp_heading': 1.5, 'kp_longitudinal': 0.6,
            'lane_timeout_s': 0.5, 'qr_timeout_s': 0.5,
            'camera_timeout_s': 0.7, 'min_lane_confidence': 0.3,
            'min_qr_confidence': 0.3, 'target_stop_distance_m': 0.55,
            'longitudinal_tolerance_m': 0.05, 'settle_cycles': 8,
            'front_camera_frame': 'camera_front_optical_frame',
            'rear_camera_frame': 'camera_rear_optical_frame',
            'rear_camera_topic': '/camera/image_raw',
            'lane_command_topic': '/cmd_vel_lane',
            'lane_active_topic': '/lane_tracking/active',
            'task_command_topic': '/task_command',
            'filtered_odom_topic': '/odometry/filtered',
            'lane_command_timeout_s': 0.30,
            'lane_active_timeout_s': 0.50,
            'activation_timeout_s': 2.0,
            'zero_command_timeout_s': 0.40,
            'odom_timeout_s': 0.50,
            'stop_timeout_s': 3.0,
            'stop_settle_s': 0.40,
            'stop_linear_tolerance': 0.01,
            'stop_angular_tolerance': 0.03,
            'reverse_angular_sign': -1.0}
        for name, value in defaults.items():
            self.declare_parameter(name, value)
        self._p = {
            name: self.get_parameter(name).value for name in defaults}
        self._cb = ReentrantCallbackGroup()
        self._lane = self._qr = None
        self._lane_valid = self._qr_valid = None
        self._lane_wall = self._qr_wall = 0.0
        self._lane_valid_wall = self._qr_valid_wall = 0.0
        self._estop = self._obstacle = False
        self._lane_command = Twist()
        self._lane_command_wall = 0.0
        self._lane_active = False
        self._lane_active_wall = 0.0
        self._camera_wall = 0.0
        self._odom_wall = 0.0
        self._linear_speed = self._angular_speed = 0.0
        self._busy = False
        self._busy_lock = threading.Lock()
        self.create_subscription(LaneOffset, '/lane/offset', self._on_lane,
                                 qos_profile_sensor_data,
                                 callback_group=self._cb)
        self.create_subscription(QrDetection, '/qr/detection', self._on_qr,
                                 qos_profile_sensor_data,
                                 callback_group=self._cb)
        self.create_subscription(Bool, '/base/estop', self._on_estop, 10,
                                 callback_group=self._cb)
        self.create_subscription(
            Bool, '/safety/obstacle_detected', self._on_obstacle,
            10, callback_group=self._cb)
        self.create_subscription(
            Twist, str(self._p['lane_command_topic']), self._on_lane_command,
            10, callback_group=self._cb)
        self.create_subscription(
            Bool, str(self._p['lane_active_topic']), self._on_lane_active,
            10, callback_group=self._cb)
        self.create_subscription(
            Image, str(self._p['rear_camera_topic']), self._on_camera,
            qos_profile_sensor_data, callback_group=self._cb)
        self.create_subscription(
            Odometry, str(self._p['filtered_odom_topic']), self._on_odom,
            10, callback_group=self._cb)
        self._pub = self.create_publisher(Twist, '/cmd_vel_dock', 10)
        self._task_pub = self.create_publisher(
            String, str(self._p['task_command_topic']), 10)
        self._server = ActionServer(self, DockToStation, 'dock_to_station',
                                    execute_callback=self._execute,
                                    goal_callback=self._goal,
                                    cancel_callback=(
                                        lambda _: CancelResponse.ACCEPT),
                                    callback_group=self._cb)

    def _on_lane(self, msg):
        self._lane, self._lane_wall = msg, time.monotonic()
        if (msg.detected
                and msg.confidence >= float(self._p['min_lane_confidence'])
                and self._finite(msg.lateral_offset, msg.heading_error,
                                 msg.confidence)):
            self._lane_valid, self._lane_valid_wall = msg, self._lane_wall

    def _on_qr(self, msg):
        self._qr, self._qr_wall = msg, time.monotonic()
        if (msg.detected
                and msg.confidence >= float(self._p['min_qr_confidence'])
                and self._finite(msg.pose_in_camera.x, msg.pose_in_camera.y,
                                 msg.pose_in_camera.theta, msg.confidence)):
            self._qr_valid, self._qr_valid_wall = msg, self._qr_wall

    def _on_estop(self, msg):
        self._estop = bool(msg.data)

    def _on_obstacle(self, msg):
        self._obstacle = bool(msg.data)

    def _on_lane_command(self, msg):
        self._lane_command, self._lane_command_wall = msg, time.monotonic()

    def _on_lane_active(self, msg):
        self._lane_active = bool(msg.data)
        self._lane_active_wall = time.monotonic()

    def _on_camera(self, _msg):
        self._camera_wall = time.monotonic()

    def _on_odom(self, msg):
        self._odom_wall = time.monotonic()
        self._linear_speed = float(msg.twist.twist.linear.x)
        self._angular_speed = float(msg.twist.twist.angular.z)

    def _goal(self, _request):
        duration = float(_request.line_follow_duration_s)
        if duration != 0.0 and (
                not math.isfinite(duration) or not 0.1 <= duration <= 120.0):
            return GoalResponse.REJECT
        with self._busy_lock:
            if self._busy:
                return GoalResponse.REJECT
            # Reserve immediately; closes the simultaneous-goal race.
            self._busy = True
        return GoalResponse.ACCEPT

    def _stop(self):
        self._pub.publish(Twist())

    def _lane_stop(self):
        self._task_pub.publish(String(data='STOP'))
        self._stop()

    @staticmethod
    def _finite(*values):
        return all(math.isfinite(float(v)) for v in values)

    def _finish(self, handle, result, code, message, canceled=False):
        self._stop()
        result.success = code == DockToStation.Result.RESULT_OK
        result.result_code, result.message = code, message
        if canceled:
            handle.canceled()
        elif result.success:
            handle.succeed()
        else:
            handle.abort()
        return result

    def _execute(self, handle):
        if float(handle.request.line_follow_duration_s) > 0.0:
            return self._execute_timed_rear_lane(handle)
        return self._execute_legacy(handle)

    def _timed_feedback(self, handle, duration, started, now, stopped=False):
        feedback = DockToStation.Feedback()
        elapsed = max(0.0, now - started) if started else 0.0
        feedback.phase = 'settling' if stopped else (
            'timed_reverse_lane' if started else 'activating_lane')
        feedback.configured_duration_s = float(duration)
        feedback.elapsed_s = float(min(duration, elapsed))
        feedback.remaining_s = float(max(0.0, duration - elapsed))
        feedback.lane_control_active = bool(self._lane_active)
        feedback.camera_valid = bool(
            self._camera_wall
            and now - self._camera_wall <= float(self._p['camera_timeout_s']))
        feedback.stopped = bool(stopped)
        handle.publish_feedback(feedback)

    def _timed_failure(self, handle, result, code, message, canceled=False):
        self._lane_stop()
        return self._finish(handle, result, code, message, canceled=canceled)

    def _wait_for_measured_stop(self, handle, result, duration, started):
        deadline = time.monotonic() + float(self._p['stop_timeout_s'])
        stable_since = None
        while rclpy.ok() and time.monotonic() < deadline:
            now = time.monotonic()
            self._lane_stop()
            if handle.is_cancel_requested:
                return self._timed_failure(
                    handle, result, DockToStation.Result.RESULT_ABORTED,
                    'docking durusunda iptal', canceled=True)
            odom_fresh = (
                self._odom_wall
                and now - self._odom_wall <= float(self._p['odom_timeout_s']))
            stopped = (
                odom_fresh
                and abs(self._linear_speed) <=
                float(self._p['stop_linear_tolerance'])
                and abs(self._angular_speed) <=
                float(self._p['stop_angular_tolerance']))
            self._timed_feedback(
                handle, duration, started, now, stopped=stopped)
            if stopped:
                stable_since = stable_since or now
                if now - stable_since >= float(self._p['stop_settle_s']):
                    return None
            else:
                stable_since = None
            time.sleep(1.0 / float(self._p['control_rate_hz']))
        return self._timed_failure(
            handle, result, DockToStation.Result.RESULT_STOP_FAILED,
            'sureli docking sonrasi olculen hiz sifira inmedi')

    def _execute_timed_rear_lane(self, handle):
        """Adapt the real lane controller to bounded reverse docking."""
        result = DockToStation.Result()
        goal = handle.request
        duration = float(goal.line_follow_duration_s)
        rate = 1.0 / float(self._p['control_rate_hz'])
        deadline = time.monotonic() + (goal.timeout or duration + 8.0)
        activation_deadline = time.monotonic() + float(
            self._p['activation_timeout_s'])
        requested_at = time.monotonic()
        started = None
        zero_since = None
        if not goal.reverse_motion or goal.camera_source != 'rear_camera':
            with self._busy_lock:
                self._busy = False
            return self._timed_failure(
                handle, result, DockToStation.Result.RESULT_ABORTED,
                'F7C yalniz reverse_motion + rear_camera kabul eder')
        self._task_pub.publish(String(data='START_LANE'))
        try:
            while rclpy.ok():
                now = time.monotonic()
                if handle.is_cancel_requested:
                    return self._timed_failure(
                        handle, result, DockToStation.Result.RESULT_ABORTED,
                        'cancel edildi', canceled=True)
                if self._estop:
                    return self._timed_failure(
                        handle, result, DockToStation.Result.RESULT_ABORTED,
                        'e-stop')
                if self._obstacle:
                    return self._timed_failure(
                        handle, result, DockToStation.Result.RESULT_OBSTACLE,
                        'engel')
                if now > deadline:
                    return self._timed_failure(
                        handle, result, DockToStation.Result.RESULT_TIMEOUT,
                        'zaman asimi')
                camera_ok = (
                    self._camera_wall > requested_at
                    and now - self._camera_wall <=
                    float(self._p['camera_timeout_s']))
                active_ok = (
                    self._lane_active and self._lane_active_wall > requested_at
                    and now - self._lane_active_wall <=
                    float(self._p['lane_active_timeout_s']))
                command_ok = (
                    self._lane_command_wall > requested_at
                    and now - self._lane_command_wall <=
                    float(self._p['lane_command_timeout_s']))
                lane_values = (
                    self._lane_command.linear.x,
                    self._lane_command.angular.z,
                )
                lane_finite = all(
                    math.isfinite(float(value)) for value in lane_values)
                command_ready = (
                    command_ok and lane_finite
                    and abs(float(self._lane_command.linear.x)) > 1e-4)
                if started is None:
                    self._stop()
                    self._task_pub.publish(String(data='START_LANE'))
                    self._timed_feedback(handle, duration, None, now)
                    if camera_ok and active_ok and command_ready:
                        started = now
                    elif now >= activation_deadline:
                        code = (DockToStation.Result.RESULT_CAMERA_LOST
                                if not camera_ok else
                                DockToStation.Result.RESULT_CONTROL_INACTIVE)
                        return self._timed_failure(
                            handle, result, code,
                            'arka kamera/serit kontrolu aktiflesmedi')
                    time.sleep(rate)
                    continue
                if not camera_ok:
                    return self._timed_failure(
                        handle, result,
                        DockToStation.Result.RESULT_CAMERA_LOST,
                        'arka kamera bayat/kayip')
                if not active_ok or not command_ok:
                    return self._timed_failure(
                        handle, result,
                        DockToStation.Result.RESULT_CONTROL_INACTIVE,
                        'serit kontrolu bayat/pasif')
                if not lane_finite:
                    return self._timed_failure(
                        handle, result,
                        DockToStation.Result.RESULT_CONTROL_INACTIVE,
                        'serit kontrolu sonlu olmayan komut uretti')
                lane = self._lane_command
                moving = abs(float(lane.linear.x)) > 1e-4
                if moving:
                    zero_since = None
                else:
                    zero_since = zero_since or now
                    if now - zero_since > float(
                            self._p['zero_command_timeout_s']):
                        return self._timed_failure(
                            handle, result,
                            DockToStation.Result.RESULT_LANE_LOST,
                            'serit kaybi: hareket komutu sifir kaldi')
                elapsed = now - started
                if elapsed >= duration:
                    stop_result = self._wait_for_measured_stop(
                        handle, result, duration, started)
                    if stop_result is not None:
                        return stop_result
                    result.final_position_error = math.nan
                    result.final_longitudinal_error = math.nan
                    result.final_yaw_error = math.nan
                    return self._finish(
                        handle, result, DockToStation.Result.RESULT_OK,
                        'sureli geri serit docking tamamlandi')
                try:
                    cmd = reverse_lane_command(
                        lane, self._p['reverse_angular_sign'],
                        self._p['max_linear_vel'],
                        self._p['max_angular_vel'])
                except ValueError:
                    return self._timed_failure(
                        handle, result,
                        DockToStation.Result.RESULT_CONTROL_INACTIVE,
                        'serit kontrolu sonlu olmayan komut uretti')
                self._pub.publish(cmd)
                self._timed_feedback(handle, duration, started, now)
                time.sleep(rate)
        finally:
            self._lane_stop()
            with self._busy_lock:
                self._busy = False
        return result

    def _execute_legacy(self, handle):
        result = DockToStation.Result()
        goal = handle.request
        rate = 1.0 / float(self._p['control_rate_hz'])
        pos_tol = goal.position_tolerance or 0.075
        yaw_tol = goal.yaw_tolerance or 0.087
        long_tol = float(self._p['longitudinal_tolerance_m'])
        target = float(self._p['target_stop_distance_m'])
        # Legacy behavior: pickup uses rear camera; dropoff uses front.
        rear = goal.approach_type == DockToStation.Goal.APPROACH_PICKUP
        frame_key = 'rear_camera_frame' if rear else 'front_camera_frame'
        frame = str(self._p[frame_key])
        direction = -1.0 if rear else 1.0
        deadline = time.monotonic() + (goal.timeout or 60.0)
        sensor_deadline = (
            time.monotonic() + float(self._p['camera_timeout_s']))
        settle = 0
        try:
            while rclpy.ok():
                now = time.monotonic()
                if handle.is_cancel_requested:
                    return self._finish(handle, result,
                                        DockToStation.Result.RESULT_ABORTED,
                                        'cancel edildi', canceled=True)
                if self._estop:
                    return self._finish(handle, result,
                                        DockToStation.Result.RESULT_ABORTED,
                                        'e-stop')
                if self._obstacle:
                    return self._finish(handle, result,
                                        DockToStation.Result.RESULT_OBSTACLE,
                                        'engel')
                if now > deadline:
                    return self._finish(handle, result,
                                        DockToStation.Result.RESULT_TIMEOUT,
                                        'zaman asimi')
                lane, qr = self._lane_valid, self._qr_valid
                if (lane is None or qr is None) and now <= sensor_deadline:
                    self._stop()
                    time.sleep(rate)
                    continue
                lane_stale = (lane is None or now - self._lane_valid_wall >
                              float(self._p['lane_timeout_s']))
                qr_stale = (qr is None or now - self._qr_valid_wall >
                            float(self._p['qr_timeout_s']))
                if (lane_stale or qr_stale) and now <= sensor_deadline:
                    self._stop()
                    time.sleep(rate)
                    continue
                if lane_stale:
                    return self._finish(
                        handle, result,
                        DockToStation.Result.RESULT_LANE_LOST,
                        'LaneOffset stale/kayip')
                if qr_stale:
                    return self._finish(
                        handle, result,
                        DockToStation.Result.RESULT_CAMERA_LOST,
                        'QR/kamera stale/kayip')
                if lane.camera_frame != frame or qr.camera_frame != frame:
                    return self._finish(
                        handle, result,
                        DockToStation.Result.RESULT_CAMERA_LOST,
                        'yanlis kamera')
                if qr.data != goal.station_id:
                    return self._finish(
                        handle, result,
                        DockToStation.Result.RESULT_QR_MISMATCH,
                        'QR uyusmazligi')
                lat = float(lane.lateral_offset)
                yaw = float(lane.heading_error)
                longitudinal = float(qr.pose_in_camera.x) - target
                result.final_position_error = abs(lat)
                result.final_longitudinal_error = abs(longitudinal)
                result.final_yaw_error = abs(yaw)
                feedback = DockToStation.Feedback()
                feedback.phase = 'settling' if settle else 'final_approach'
                feedback.position_error = abs(lat)
                feedback.yaw_error = abs(yaw)
                feedback.distance_remaining = abs(longitudinal)
                handle.publish_feedback(feedback)
                within = (abs(lat) <= pos_tol and abs(yaw) <= yaw_tol and
                          abs(longitudinal) <= long_tol)
                settle = settle + 1 if within else 0
                if settle >= int(self._p['settle_cycles']):
                    return self._finish(
                        handle, result, DockToStation.Result.RESULT_OK,
                        'docking basarili')
                cmd = Twist()
                max_linear = float(self._p['max_linear_vel'])
                cmd.linear.x = direction * max(
                    -max_linear,
                    min(
                        max_linear,
                        float(self._p['kp_longitudinal']) * longitudinal))
                max_angular = float(self._p['max_angular_vel'])
                cmd.angular.z = max(
                    -max_angular,
                    min(
                        max_angular,
                        direction * (
                            float(self._p['kp_heading']) * yaw
                            + float(self._p['kp_lateral']) * lat)))
                self._pub.publish(cmd)
                time.sleep(rate)
        finally:
            self._stop()
            with self._busy_lock:
                self._busy = False
        return result


def main():
    rclpy.init()
    node = DockServer()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        if rclpy.ok():
            node._stop()
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
