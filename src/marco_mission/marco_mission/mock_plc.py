#!/usr/bin/env python3
"""
Sahte PLC — AssignTask / GatePermission / TaskComplete servisleri.

Gercek PLC protokolu gelince ayni servis imzalari korunur; bu dugum yerine
protokol koprusu konur.

  ros2 run marco_mission mock_plc.py
"""

from __future__ import annotations

import random
import time
import uuid

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from std_msgs.msg import Float32

from marco_msgs.srv import AssignTask, GatePermission, TaskComplete


class MockPlc(Node):
    """Yarisma PLC davranisinin soyut modeli."""

    def __init__(self) -> None:
        super().__init__("mock_plc")
        self.declare_parameter(
            "pickup_nodes",
            ["alma_1", "alma_2", "alma_3"],
        )
        self.declare_parameter(
            "dropoff_nodes",
            ["birak_1", "birak_2", "birak_3"],
        )
        self.declare_parameter("gate_node", "kapi_q5")
        self.declare_parameter("gate_delay_s", 0.5)
        self.declare_parameter("gate_granted", True)
        self.declare_parameter("connected", True)

        self._pickups = list(self.get_parameter("pickup_nodes").value)
        self._dropoffs = list(self.get_parameter("dropoff_nodes").value)
        self._gate = str(self.get_parameter("gate_node").value)
        self._gate_delay = float(self.get_parameter("gate_delay_s").value)
        self._gate_granted = bool(self.get_parameter("gate_granted").value)
        self._connected = bool(self.get_parameter("connected").value)
        self._last_pair = None
        self._heartbeat = self.create_publisher(Bool, '/plc/connected', 10)
        self.create_subscription(Bool, '/plc/test_connected',
                                 lambda m: setattr(self, '_connected', bool(m.data)), 10)
        self.create_subscription(Bool, '/plc/test_gate_granted',
                                 lambda m: setattr(self, '_gate_granted', bool(m.data)), 10)
        self.create_subscription(Float32, '/plc/test_gate_delay',
                                 lambda m: setattr(self, '_gate_delay', float(m.data)), 10)
        self.create_timer(0.2, self._publish_heartbeat)

        self.create_service(AssignTask, "/plc/assign_task", self._on_assign)
        self.create_service(GatePermission, "/plc/gate_permission", self._on_gate)
        self.create_service(TaskComplete, "/plc/task_complete", self._on_complete)
        self.get_logger().info(
            f"mock_plc hazir | pickups={self._pickups} dropoffs={self._dropoffs} "
            f"gate={self._gate}"
        )

    def _publish_heartbeat(self) -> None:
        self._heartbeat.publish(Bool(data=self._connected))

    def _on_assign(
        self, _req: AssignTask.Request, res: AssignTask.Response
    ) -> AssignTask.Response:
        if not self._pickups or not self._dropoffs:
            res.success = False
            res.message = "alma/birakma listesi bos"
            return res
        res.success = True
        choices = [(p, d) for p in self._pickups for d in self._dropoffs]
        if len(choices) > 1 and self._last_pair in choices:
            choices.remove(self._last_pair)
        res.pickup_node, res.dropoff_node = random.choice(choices)
        self._last_pair = (res.pickup_node, res.dropoff_node)
        res.task_id = f"task_{uuid.uuid4().hex[:8]}"
        res.message = "gorev atandi"
        self.get_logger().info(
            f"AssignTask → {res.task_id} {res.pickup_node}→{res.dropoff_node}"
        )
        return res

    def _on_gate(
        self, req: GatePermission.Request, res: GatePermission.Response
    ) -> GatePermission.Response:
        node_id = req.node_id or self._gate
        if self._gate_delay > 0:
            time.sleep(self._gate_delay)
        res.granted = self._gate_granted and self._connected
        res.message = (f"gecis izni: {node_id}" if res.granted else
                       f"gecis reddedildi: {node_id}")
        self.get_logger().info(f"GatePermission granted for {node_id}")
        return res

    def _on_complete(
        self, req: TaskComplete.Request, res: TaskComplete.Response
    ) -> TaskComplete.Response:
        res.acknowledged = True
        self.get_logger().info(
            f"TaskComplete ack task={req.task_id} success={req.success} "
            f"msg={req.message}"
        )
        return res


def main() -> None:
    rclpy.init()
    node = MockPlc()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
