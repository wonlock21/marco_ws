"""Fail-closed tests for the production PLC bridge placeholder."""

import rclpy

from marco_msgs.msg import RobotStatus
from marco_msgs.srv import AssignTask, GatePermission, TaskComplete
from marco_plc.plc_bridge_node import PlcBridgeNode
from marco_plc.transports.base import (
    CompletionResult,
    GatePermissionResult,
    PlcTransport,
    TaskAssignmentResult,
)


class RecordingTransport(PlcTransport):
    """Connected test transport that records the protocol-neutral snapshot."""

    def __init__(self):
        self.status = None

    def connect(self):
        return True

    def disconnect(self):
        pass

    def is_connected(self):
        return True

    def update_robot_status(self, status):
        self.status = status

    def request_task(self):
        return TaskAssignmentResult(False)

    def request_gate_permission(
        self, task_id, crossing_id, node_id, direction
    ):
        del task_id, node_id, direction
        return GatePermissionResult(False, crossing_id)

    def report_task_complete(self, task_id, success, message):
        del task_id, success, message
        return CompletionResult(False)


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


def test_robot_status_is_reduced_to_map_frame_transport_snapshot():
    """Pass only mission, assignment and map pose data into the transport."""
    rclpy.init()
    transport = RecordingTransport()
    node = PlcBridgeNode(transport=transport)
    try:
        message = RobotStatus()
        message.pose.header.frame_id = 'map'
        message.mission_state = RobotStatus.STATE_MOVING_LOADED
        message.pickup_node = 'A3'
        message.dropoff_node = 'B2'
        message.pose.pose.pose.position.x = 1.25
        message.pose.pose.pose.position.y = -0.75
        node._on_robot_status(message)

        assert transport.status.mission_state == RobotStatus.STATE_MOVING_LOADED
        assert transport.status.pickup_node == 'A3'
        assert transport.status.dropoff_node == 'B2'
        assert transport.status.x_m == 1.25
        assert transport.status.y_m == -0.75
    finally:
        node.destroy_node()
        rclpy.shutdown()
