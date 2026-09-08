"""PLC transport contracts and fail-safe placeholder implementations."""

from marco_plc.transports.base import (
    CompletionResult,
    GatePermissionResult,
    PlcTransport,
    TaskAssignmentResult,
    UnconfiguredTransport,
)

__all__ = [
    'CompletionResult',
    'GatePermissionResult',
    'PlcTransport',
    'TaskAssignmentResult',
    'UnconfiguredTransport',
]
