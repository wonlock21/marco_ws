"""Protocol-neutral contract implemented by future PLC transports."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RobotStatusSnapshot:
    """Protocol-neutral subset of RobotStatus required by PLC transports."""

    mission_state: int
    pickup_node: str
    dropoff_node: str
    x_m: float
    y_m: float


@dataclass(frozen=True)
class TaskAssignmentResult:
    """Result of requesting one task from the PLC."""

    success: bool
    task_id: str = ''
    pickup_node: str = ''
    dropoff_node: str = ''
    message: str = ''


@dataclass(frozen=True)
class GatePermissionResult:
    """Result of requesting one direction-specific gate crossing."""

    granted: bool
    crossing_id: str
    message: str = ''


@dataclass(frozen=True)
class CompletionResult:
    """Result of reporting mission completion to the PLC."""

    acknowledged: bool
    message: str = ''


class PlcTransport(ABC):
    """Define the protocol-independent operations required by the ROS bridge."""

    @abstractmethod
    def connect(self) -> bool:
        """Attempt a bounded connection and return whether it is usable."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close transport resources without raising during shutdown."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Return whether requests can currently reach the PLC."""

    @abstractmethod
    def update_robot_status(self, status: RobotStatusSnapshot) -> None:
        """Cache the latest robot state without performing blocking I/O."""

    @abstractmethod
    def request_task(self) -> TaskAssignmentResult:
        """Request a task assignment from the PLC."""

    @abstractmethod
    def request_gate_permission(
        self,
        task_id: str,
        crossing_id: str,
        node_id: str,
        direction: str,
    ) -> GatePermissionResult:
        """Request permission for one identified gate crossing."""

    @abstractmethod
    def report_task_complete(
        self, task_id: str, success: bool, message: str
    ) -> CompletionResult:
        """Report the terminal result of a task."""


class UnconfiguredTransport(PlcTransport):
    """Fail closed while no field protocol implementation is configured."""

    def __init__(self, reason: str = 'PLC transport yapilandirilmadi') -> None:
        self.reason = reason

    def connect(self) -> bool:
        """Refuse to synthesize a connection."""
        return False

    def disconnect(self) -> None:
        """Perform the no-op shutdown required by the common contract."""

    def is_connected(self) -> bool:
        """Remain disconnected by definition."""
        return False

    def update_robot_status(self, status: RobotStatusSnapshot) -> None:
        """Discard telemetry because no wire transport is configured."""
        del status

    def request_task(self) -> TaskAssignmentResult:
        """Reject task requests while unconfigured."""
        return TaskAssignmentResult(success=False, message=self.reason)

    def request_gate_permission(
        self,
        task_id: str,
        crossing_id: str,
        node_id: str,
        direction: str,
    ) -> GatePermissionResult:
        """Deny every gate request while unconfigured."""
        del task_id, node_id, direction
        return GatePermissionResult(
            granted=False,
            crossing_id=crossing_id,
            message=self.reason,
        )

    def report_task_complete(
        self, task_id: str, success: bool, message: str
    ) -> CompletionResult:
        """Refuse to acknowledge a report that did not reach a PLC."""
        del task_id, success, message
        return CompletionResult(acknowledged=False, message=self.reason)
