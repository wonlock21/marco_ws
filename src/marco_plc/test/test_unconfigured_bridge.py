"""Fail-closed tests for the production PLC bridge placeholder."""

import rclpy

from marco_msgs.srv import AssignTask, GatePermission, TaskComplete
from marco_plc.plc_bridge_node import PlcBridgeNode


def test_unconfigured_bridge_starts_and_denies_all_operations():
    """Start normally but never grant or acknowledge without a transport."""
    rclpy.init()
    node = PlcBridgeNode()
    try:
        assert node.connected is False
        assert node._connection_message().data is False

        assignment = node._on_assign(
            AssignTask.Request(), AssignTask.Response())
        assert assignment.success is False

        gate_request = GatePermission.Request()
        gate_request.task_id = 'task-1'
        gate_request.crossing_id = 'task-1:1:outbound'
        gate_request.node_id = 'q5'
        gate_request.direction = 'outbound'
        gate = node._on_gate(gate_request, GatePermission.Response())
        assert gate.granted is False
        assert gate.crossing_id == gate_request.crossing_id

        complete = node._on_complete(
            TaskComplete.Request(), TaskComplete.Response())
        assert complete.acknowledged is False
    finally:
        node.destroy_node()
        rclpy.shutdown()
