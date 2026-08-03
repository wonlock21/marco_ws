#!/usr/bin/env python3
"""Gorev durum makinesi + GUI durum yayini (Faz 10 arayuz).

PLC protokolu bilinmedigi icin navigasyon/docking cagrilari varsayilan
simule edilir (simulate_steps:=true). Gercek Nav2/dock baglantisi sonra
ayni durum gecislerine eklenir.

Yayin:  /robot_status          marco_msgs/RobotStatus
Servis: /mission/start         marco_msgs/StartMission
Istem:  /plc/assign_task, /plc/gate_permission, /plc/task_complete

  ros2 launch marco_mission mission.launch.py
  ros2 service call /mission/start marco_msgs/srv/StartMission "{}"
"""

from __future__ import annotations

import threading
import time
from typing import Optional

import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import Bool

from marco_msgs.msg import RobotStatus
from marco_msgs.srv import (
    AssignTask,
    GatePermission,
    StartMission,
    TaskComplete,
)


class MissionManager(Node):
    """Sartname senaryo akisinin durum makinesi."""

    def __init__(self) -> None:
        super().__init__("mission_manager")
        self.declare_parameter("status_rate_hz", 5.0)
        self.declare_parameter("simulate_steps", True)
        self.declare_parameter("step_delay_s", 1.0)
        self.declare_parameter("gate_node", "kapi_q5")

        rate = float(self.get_parameter("status_rate_hz").value)
        self._simulate = bool(self.get_parameter("simulate_steps").value)
        self._step_delay = float(self.get_parameter("step_delay_s").value)
        self._gate_node = str(self.get_parameter("gate_node").value)

        self._cb = ReentrantCallbackGroup()
        self._lock = threading.Lock()
        self._busy = False

        self._mission_state = RobotStatus.STATE_IDLE
        self._task_id = ""
        self._pickup = ""
        self._dropoff = ""
        self._next_node = ""
        self._route_edge = ""
        self._plc_connected = False
        self._gate_ok = False
        self._estop = False
        self._manual = False
        self._obstacle = False
        self._loc_valid = True
        self._last_qr = ""

        self._status_pub = self.create_publisher(RobotStatus, "/robot_status", 10)
        self.create_subscription(
            Bool, "/base/estop", self._on_estop, 10, callback_group=self._cb
        )
        self.create_subscription(
            Bool, "/base/manual_mode", self._on_manual, 10, callback_group=self._cb
        )
        self.create_subscription(
            Bool, "/safety/obstacle_detected", self._on_obstacle, 10,
            callback_group=self._cb
        )
        self.create_subscription(
            Bool, "/safety/navigation_abort", self._on_safety_abort, 10,
            callback_group=self._cb
        )

        self._cli_assign = self.create_client(
            AssignTask, "/plc/assign_task", callback_group=self._cb
        )
        self._cli_gate = self.create_client(
            GatePermission, "/plc/gate_permission", callback_group=self._cb
        )
        self._cli_done = self.create_client(
            TaskComplete, "/plc/task_complete", callback_group=self._cb
        )

        self.create_service(
            StartMission,
            "/mission/start",
            self._on_start,
            callback_group=self._cb,
        )
        self.create_timer(1.0 / rate, self._publish_status)
        self.get_logger().info(
            f"mission_manager hazir | simulate_steps={self._simulate} | "
            "/mission/start → gorev dongusu"
        )

    def _on_estop(self, msg: Bool) -> None:
        self._estop = bool(msg.data)
        if self._estop:
            self._mission_state = RobotStatus.STATE_ESTOP

    def _on_manual(self, msg: Bool) -> None:
        self._manual = bool(msg.data)

    def _on_obstacle(self, msg: Bool) -> None:
        """Use only the measured safety supervisor state, never an estimate."""
        self._obstacle = bool(msg.data)

    def _on_safety_abort(self, msg: Bool) -> None:
        if msg.data and self._busy:
            self._fail("guvenlik engel bekleme zaman asimi")

    def _publish_status(self) -> None:
        msg = RobotStatus()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "map"
        msg.mission_state = self._mission_state
        msg.manual_mode_enabled = self._manual
        msg.estop_active = self._estop
        msg.pose = PoseWithCovarianceStamped()
        msg.pose.header = msg.header
        msg.localization_valid = self._loc_valid
        msg.position_covariance = 0.0
        msg.current_route_edge = self._route_edge
        msg.next_node = self._next_node
        msg.cross_track_error = 0.0
        msg.obstacle_detected = self._obstacle
        msg.task_id = self._task_id
        msg.pickup_node = self._pickup
        msg.dropoff_node = self._dropoff
        msg.last_qr_data = self._last_qr
        msg.plc_connected = self._plc_connected
        msg.gate_permission_granted = self._gate_ok
        self._status_pub.publish(msg)

    def _on_start(
        self, _req: StartMission.Request, res: StartMission.Response
    ) -> StartMission.Response:
        with self._lock:
            if self._busy:
                res.accepted = False
                res.message = "gorev zaten suruyor"
                return res
            if self._estop:
                res.accepted = False
                res.message = "e-stop aktif"
                return res
            self._busy = True
        threading.Thread(target=self._run_mission, daemon=True).start()
        res.accepted = True
        res.message = "gorev baslatildi"
        return res

    def _wait_service(self, client, name: str, timeout: float = 5.0) -> bool:
        if client.wait_for_service(timeout_sec=timeout):
            return True
        self.get_logger().error(f"{name} servisi yok")
        return False

    def _call(self, client, request, timeout: float = 10.0):
        future = client.call_async(request)
        t0 = time.monotonic()
        while rclpy.ok() and not future.done():
            if time.monotonic() - t0 > timeout:
                return None
            time.sleep(0.05)
        return future.result()

    def _set_state(
        self,
        state: int,
        next_node: Optional[str] = None,
        edge: Optional[str] = None,
    ) -> None:
        self._mission_state = state
        if next_node is not None:
            self._next_node = next_node
        if edge is not None:
            self._route_edge = edge
        self.get_logger().info(
            f"STATE={state} next={self._next_node} edge={self._route_edge} "
            f"task={self._task_id}"
        )

    def _sim_travel(self, label: str) -> None:
        if not self._simulate:
            return
        self.get_logger().info(f"[sim] {label} ({self._step_delay:.1f}s)")
        time.sleep(self._step_delay)

    def _run_mission(self) -> None:
        try:
            self._gate_ok = False
            self._plc_connected = False
            self._set_state(RobotStatus.STATE_TASK_RECEIVED)

            if not self._wait_service(self._cli_assign, "/plc/assign_task"):
                self._fail("PLC assign_task yok")
                return
            self._plc_connected = True

            assign = self._call(self._cli_assign, AssignTask.Request())
            if assign is None or not assign.success:
                self._fail(assign.message if assign else "assign timeout")
                return

            self._task_id = assign.task_id
            self._pickup = assign.pickup_node
            self._dropoff = assign.dropoff_node
            self.get_logger().info(
                f"gorev alindi: {self._task_id} {self._pickup}→{self._dropoff}"
            )

            # Alma
            self._set_state(
                RobotStatus.STATE_MOVING_UNLOADED,
                next_node=self._pickup,
                edge=f"start→{self._pickup}",
            )
            self._sim_travel(f"alma noktasina git: {self._pickup}")
            self._last_qr = self._pickup
            self._sim_travel("docking/alma (QR+serit)")

            # Yuklu → kapi
            self._set_state(
                RobotStatus.STATE_MOVING_LOADED,
                next_node=self._gate_node,
                edge=f"{self._pickup}→{self._gate_node}",
            )
            self._sim_travel(f"kapiya git: {self._gate_node}")

            self._set_state(RobotStatus.STATE_WAITING_PLC, next_node=self._gate_node)
            if not self._wait_service(self._cli_gate, "/plc/gate_permission"):
                self._fail("PLC gate_permission yok")
                return
            gate_req = GatePermission.Request()
            gate_req.node_id = self._gate_node
            gate = self._call(self._cli_gate, gate_req)
            if gate is None or not gate.granted:
                self._fail(gate.message if gate else "gate timeout")
                return
            self._gate_ok = True

            # Birakma
            self._set_state(
                RobotStatus.STATE_MOVING_LOADED,
                next_node=self._dropoff,
                edge=f"{self._gate_node}→{self._dropoff}",
            )
            self._sim_travel(f"birakma noktasina git: {self._dropoff}")
            self._last_qr = self._dropoff
            self._sim_travel("docking/birakma (QR+serit)")

            # Donus
            self._set_state(
                RobotStatus.STATE_RETURNING,
                next_node="bekla_A",
                edge=f"{self._dropoff}→bekla_A",
            )
            self._sim_travel("bekleme noktasina don")

            if self._wait_service(self._cli_done, "/plc/task_complete", timeout=3.0):
                done = TaskComplete.Request()
                done.task_id = self._task_id
                done.success = True
                done.message = "gorev tamam"
                self._call(self._cli_done, done, timeout=5.0)

            self._set_state(RobotStatus.STATE_IDLE, next_node="", edge="")
            self.get_logger().info(f"gorev bitti: {self._task_id}")
        except Exception as exc:  # noqa: BLE001 — durum makinesinde yakala
            self._fail(str(exc))
        finally:
            with self._lock:
                self._busy = False

    def _fail(self, message: str) -> None:
        self.get_logger().error(f"gorev hata: {message}")
        self._mission_state = RobotStatus.STATE_ERROR
        self._route_edge = ""
        if self._task_id and self._cli_done.service_is_ready():
            done = TaskComplete.Request()
            done.task_id = self._task_id
            done.success = False
            done.message = message
            self._call(self._cli_done, done, timeout=3.0)


def main() -> None:
    rclpy.init()
    node = MissionManager()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
