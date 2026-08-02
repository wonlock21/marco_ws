#!/usr/bin/env python3
"""DockToStation action server — hassas yanasma kontrolu (Faz 9).

Girdi:  /lane/offset, /qr/detection  (goruntu ekibi veya mock)
Cikti:  /cmd_vel_dock → twist_mux (nav'dan yuksek oncelik)

Fazlar: qr_verify → lane_align → final_approach → settling

  ros2 launch marco_docking docking.launch.py
  ros2 action send_goal /dock_to_station marco_msgs/action/DockToStation \\
    "{station_id: 'istasyon_A', position_tolerance: 0.075, yaw_tolerance: 0.087,
      approach_type: 0, timeout: 60.0}"
"""

from __future__ import annotations

import time
from typing import Optional

import rclpy
from geometry_msgs.msg import Twist
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.action.server import ServerGoalHandle
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from marco_msgs.action import DockToStation
from marco_msgs.msg import LaneOffset, QrDetection


class DockServer(Node):
    """Serit/QR ile kapali cevrim yanaşma."""

    def __init__(self) -> None:
        super().__init__("dock_server")
        self.declare_parameter("control_rate_hz", 20.0)
        self.declare_parameter("max_linear_vel", 0.05)
        self.declare_parameter("max_angular_vel", 0.40)
        self.declare_parameter("kp_lateral", 1.2)
        self.declare_parameter("kp_heading", 1.5)
        self.declare_parameter("lane_lost_timeout_s", 1.5)
        self.declare_parameter("settle_cycles", 10)
        self.declare_parameter("min_confidence", 0.3)
        self.declare_parameter("align_heading_tol", 0.12)
        self.declare_parameter("align_lateral_tol", 0.10)

        self._rate = float(self.get_parameter("control_rate_hz").value)
        self._vmax = float(self.get_parameter("max_linear_vel").value)
        self._wmax = float(self.get_parameter("max_angular_vel").value)
        self._kp_y = float(self.get_parameter("kp_lateral").value)
        self._kp_w = float(self.get_parameter("kp_heading").value)
        self._lost_t = float(self.get_parameter("lane_lost_timeout_s").value)
        self._settle_n = int(self.get_parameter("settle_cycles").value)
        self._min_conf = float(self.get_parameter("min_confidence").value)
        self._align_yaw = float(self.get_parameter("align_heading_tol").value)
        self._align_lat = float(self.get_parameter("align_lateral_tol").value)

        self._cb = ReentrantCallbackGroup()
        self._lane: Optional[LaneOffset] = None
        self._qr: Optional[QrDetection] = None
        self._lane_stamp = 0.0
        self._busy = False

        self.create_subscription(
            LaneOffset,
            "/lane/offset",
            self._on_lane,
            qos_profile_sensor_data,
            callback_group=self._cb,
        )
        self.create_subscription(
            QrDetection,
            "/qr/detection",
            self._on_qr,
            qos_profile_sensor_data,
            callback_group=self._cb,
        )
        self._cmd_pub = self.create_publisher(Twist, "/cmd_vel_dock", 10)

        self._server = ActionServer(
            self,
            DockToStation,
            "dock_to_station",
            execute_callback=self._execute,
            goal_callback=self._goal_cb,
            cancel_callback=self._cancel_cb,
            callback_group=self._cb,
        )
        self.get_logger().info(
            "dock_server hazir | action=/dock_to_station | cmd=/cmd_vel_dock"
        )

    def _on_lane(self, msg: LaneOffset) -> None:
        self._lane = msg
        self._lane_stamp = time.monotonic()

    def _on_qr(self, msg: QrDetection) -> None:
        self._qr = msg

    def _goal_cb(self, _goal_request: DockToStation.Goal) -> GoalResponse:
        if self._busy:
            self.get_logger().warn("docking zaten aktif — yeni hedef reddedildi")
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def _cancel_cb(self, _goal_handle: ServerGoalHandle) -> CancelResponse:
        return CancelResponse.ACCEPT

    def _stop(self) -> None:
        self._cmd_pub.publish(Twist())

    def _clamp(self, v: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, v))

    def _execute(self, goal_handle: ServerGoalHandle) -> DockToStation.Result:
        self._busy = True
        goal: DockToStation.Goal = goal_handle.request
        result = DockToStation.Result()

        pos_tol = goal.position_tolerance if goal.position_tolerance > 0 else 0.075
        yaw_tol = goal.yaw_tolerance if goal.yaw_tolerance > 0 else 0.087
        timeout = goal.timeout if goal.timeout > 0 else 60.0
        station = goal.station_id

        feedback = DockToStation.Feedback()
        t0 = time.monotonic()
        phase = "qr_verify"
        settle_ok = 0
        dt = 1.0 / self._rate

        self.get_logger().info(
            f"docking basladi station={station!r} pos_tol={pos_tol:.3f} "
            f"yaw_tol={yaw_tol:.3f} timeout={timeout:.0f}s"
        )

        try:
            while rclpy.ok():
                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    self._stop()
                    result.success = False
                    result.result_code = DockToStation.Result.RESULT_ABORTED
                    result.message = "iptal edildi"
                    return result

                now = time.monotonic()
                if now - t0 > timeout:
                    goal_handle.abort()
                    self._stop()
                    result.success = False
                    result.result_code = DockToStation.Result.RESULT_TIMEOUT
                    result.message = "zaman asimi"
                    return result

                qr = self._qr
                lane = self._lane

                if phase == "qr_verify":
                    feedback.phase = phase
                    feedback.position_error = 0.0
                    feedback.yaw_error = 0.0
                    feedback.distance_remaining = 1.5
                    goal_handle.publish_feedback(feedback)
                    if qr is not None and qr.detected and qr.confidence >= self._min_conf:
                        if qr.data != station:
                            goal_handle.abort()
                            self._stop()
                            result.success = False
                            result.result_code = DockToStation.Result.RESULT_QR_MISMATCH
                            result.message = (
                                f"QR uyusmadi: okunan={qr.data!r} beklenen={station!r}"
                            )
                            return result
                        phase = "lane_align"
                        self.get_logger().info("QR dogrulandi → lane_align")
                    self._stop()
                    time.sleep(dt)
                    continue

                # lane gerekli
                if (
                    lane is None
                    or not lane.detected
                    or lane.confidence < self._min_conf
                    or (now - self._lane_stamp) > self._lost_t
                ):
                    goal_handle.abort()
                    self._stop()
                    result.success = False
                    result.result_code = DockToStation.Result.RESULT_LANE_LOST
                    result.message = "serit kaybedildi"
                    return result

                lat = float(lane.lateral_offset)
                yaw = float(lane.heading_error)
                pos_err = abs(lat)
                yaw_err = abs(yaw)

                feedback.phase = phase
                feedback.position_error = pos_err
                feedback.yaw_error = yaw_err
                feedback.distance_remaining = max(0.0, pos_err + 0.5 * yaw_err)
                goal_handle.publish_feedback(feedback)

                cmd = Twist()
                # Pozitif lateral = serit solda → robota sola ( +vy yok, diff drive:
                # sola donmek icin +wz; ileri giderken cross-track icin -kp*lat ile
                # yaw duzeltmesi).
                w = self._clamp(
                    -self._kp_w * yaw - self._kp_y * lat,
                    -self._wmax,
                    self._wmax,
                )
                cmd.angular.z = w

                if phase == "lane_align":
                    cmd.linear.x = 0.0
                    if yaw_err < self._align_yaw and pos_err < self._align_lat:
                        phase = "final_approach"
                        self.get_logger().info("hizalama tamam → final_approach")
                elif phase == "final_approach":
                    # Yavas ileri; yan hata buyukse hizi dusur.
                    scale = self._clamp(1.0 - pos_err / 0.20, 0.2, 1.0)
                    cmd.linear.x = self._vmax * scale
                    if pos_err <= pos_tol and yaw_err <= yaw_tol:
                        phase = "settling"
                        settle_ok = 0
                        self.get_logger().info("tolerans icinde → settling")
                elif phase == "settling":
                    cmd.linear.x = 0.0
                    cmd.angular.z = self._clamp(-self._kp_w * yaw, -self._wmax * 0.5, self._wmax * 0.5)
                    if pos_err <= pos_tol and yaw_err <= yaw_tol:
                        settle_ok += 1
                    else:
                        settle_ok = 0
                        phase = "final_approach"
                    if settle_ok >= self._settle_n:
                        self._stop()
                        goal_handle.succeed()
                        result.success = True
                        result.result_code = DockToStation.Result.RESULT_OK
                        result.final_position_error = pos_err
                        result.final_yaw_error = yaw_err
                        result.message = "docking basarili"
                        self.get_logger().info(
                            f"SUCCEEDED pos_err={pos_err:.4f}m yaw_err={yaw_err:.4f}rad"
                        )
                        return result

                self._cmd_pub.publish(cmd)
                time.sleep(dt)
        finally:
            self._stop()
            self._busy = False

        goal_handle.abort()
        result.success = False
        result.result_code = DockToStation.Result.RESULT_ABORTED
        result.message = "beklenmeyen cikis"
        return result


def main() -> None:
    rclpy.init()
    node = DockServer()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node._stop()
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
