#!/usr/bin/env python3
"""Fail-safe camera lane/QR DockToStation action server."""

import math
import threading
import time

import rclpy
from geometry_msgs.msg import Twist
from marco_msgs.action import DockToStation
from marco_msgs.msg import LaneOffset, QrDetection
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import Bool


class DockServer(Node):
    """Drive only through cmd_vel_dock and require all three terminal errors."""

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
            'rear_camera_frame': 'camera_rear_optical_frame'}
        for name, value in defaults.items():
            self.declare_parameter(name, value)
        self._p = {name: self.get_parameter(name).value for name in defaults}
        self._cb = ReentrantCallbackGroup()
        self._lane = self._qr = None
        self._lane_valid = self._qr_valid = None
        self._lane_wall = self._qr_wall = 0.0
        self._lane_valid_wall = self._qr_valid_wall = 0.0
        self._estop = self._obstacle = False
        self._busy = False
        self._busy_lock = threading.Lock()
        self.create_subscription(LaneOffset, '/lane/offset', self._on_lane,
                                 qos_profile_sensor_data, callback_group=self._cb)
        self.create_subscription(QrDetection, '/qr/detection', self._on_qr,
                                 qos_profile_sensor_data, callback_group=self._cb)
        self.create_subscription(Bool, '/base/estop', self._on_estop, 10,
                                 callback_group=self._cb)
        self.create_subscription(Bool, '/safety/obstacle_detected', self._on_obstacle,
                                 10, callback_group=self._cb)
        self._pub = self.create_publisher(Twist, '/cmd_vel_dock', 10)
        self._server = ActionServer(self, DockToStation, 'dock_to_station',
                                    execute_callback=self._execute,
                                    goal_callback=self._goal,
                                    cancel_callback=lambda _: CancelResponse.ACCEPT,
                                    callback_group=self._cb)

    def _on_lane(self, msg):
        self._lane, self._lane_wall = msg, time.monotonic()
        if (msg.detected and msg.confidence >= float(self._p['min_lane_confidence'])
                and self._finite(msg.lateral_offset, msg.heading_error,
                                 msg.confidence)):
            self._lane_valid, self._lane_valid_wall = msg, self._lane_wall

    def _on_qr(self, msg):
        self._qr, self._qr_wall = msg, time.monotonic()
        if (msg.detected and msg.confidence >= float(self._p['min_qr_confidence'])
                and self._finite(msg.pose_in_camera.x, msg.pose_in_camera.y,
                                 msg.pose_in_camera.theta, msg.confidence)):
            self._qr_valid, self._qr_valid_wall = msg, self._qr_wall

    def _on_estop(self, msg):
        self._estop = bool(msg.data)

    def _on_obstacle(self, msg):
        self._obstacle = bool(msg.data)

    def _goal(self, _request):
        with self._busy_lock:
            if self._busy:
                return GoalResponse.REJECT
            self._busy = True  # reserve immediately; closes simultaneous-goal race
        return GoalResponse.ACCEPT

    def _stop(self):
        self._pub.publish(Twist())

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
        result = DockToStation.Result()
        goal = handle.request
        rate = 1.0 / float(self._p['control_rate_hz'])
        pos_tol = goal.position_tolerance or 0.075
        yaw_tol = goal.yaw_tolerance or 0.087
        long_tol = float(self._p['longitudinal_tolerance_m'])
        target = float(self._p['target_stop_distance_m'])
        # Pickup approaches forks-first through rear camera; dropoff uses front.
        rear = goal.approach_type == DockToStation.Goal.APPROACH_PICKUP
        frame = str(self._p['rear_camera_frame' if rear else 'front_camera_frame'])
        direction = -1.0 if rear else 1.0
        deadline = time.monotonic() + (goal.timeout or 60.0)
        sensor_deadline = time.monotonic() + float(self._p['camera_timeout_s'])
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
                                        DockToStation.Result.RESULT_ABORTED, 'e-stop')
                if self._obstacle:
                    return self._finish(handle, result,
                                        DockToStation.Result.RESULT_OBSTACLE, 'engel')
                if now > deadline:
                    return self._finish(handle, result,
                                        DockToStation.Result.RESULT_TIMEOUT, 'zaman asimi')
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
                    return self._finish(handle, result,
                                        DockToStation.Result.RESULT_LANE_LOST,
                                        'LaneOffset stale/kayip')
                if qr_stale:
                    return self._finish(handle, result,
                                        DockToStation.Result.RESULT_CAMERA_LOST,
                                        'QR/kamera stale/kayip')
                if lane.camera_frame != frame or qr.camera_frame != frame:
                    return self._finish(handle, result,
                                        DockToStation.Result.RESULT_CAMERA_LOST,
                                        'yanlis kamera')
                if qr.data != goal.station_id:
                    return self._finish(handle, result,
                                        DockToStation.Result.RESULT_QR_MISMATCH,
                                        'QR uyusmazligi')
                lat, yaw = float(lane.lateral_offset), float(lane.heading_error)
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
                    return self._finish(handle, result, DockToStation.Result.RESULT_OK,
                                        'docking basarili')
                cmd = Twist()
                cmd.linear.x = direction * max(-float(self._p['max_linear_vel']), min(
                    float(self._p['max_linear_vel']),
                    float(self._p['kp_longitudinal']) * longitudinal))
                cmd.angular.z = max(-float(self._p['max_angular_vel']), min(
                    float(self._p['max_angular_vel']),
                    direction * (float(self._p['kp_heading']) * yaw +
                                 float(self._p['kp_lateral']) * lat)))
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
