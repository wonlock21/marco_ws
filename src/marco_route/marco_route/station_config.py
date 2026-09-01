"""Validation and projection for station approach configuration."""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from .graph_model import FieldGraph, GraphError, NodeData


TURN_DIRECTIONS = frozenset({"left", "right", "auto"})
STATION_ROLES = frozenset({"pickup_dock", "dropoff_dock"})


def checked_values(
    approach_qr_id: str,
    dock_heading_yaw: float,
    turn_direction: str,
    line_follow_duration_s: float,
) -> dict[str, Any]:
    """Return a normalized, safe station configuration."""
    qr_id = str(approach_qr_id).strip()
    direction = str(turn_direction).strip().lower()
    yaw = float(dock_heading_yaw)
    duration = float(line_follow_duration_s)
    if not qr_id:
        raise GraphError("approach_qr_id cannot be empty")
    if len(qr_id) > 64:
        raise GraphError("approach_qr_id cannot exceed 64 characters")
    if direction not in TURN_DIRECTIONS:
        raise GraphError("turn_direction must be left, right or auto")
    if not math.isfinite(yaw):
        raise GraphError("dock_heading_yaw must be finite")
    if not math.isfinite(duration) or not 0.1 <= duration <= 120.0:
        raise GraphError("line_follow_duration_s must be between 0.1 and 120.0")
    return {
        "approach_qr_id": qr_id,
        "dock_heading_yaw": yaw,
        "turn_direction": direction,
        "line_follow_duration_s": duration,
    }


def station_node(graph: FieldGraph, station_id: str) -> NodeData:
    """Find the unique pickup/dropoff dock node for a station ID."""
    station = str(station_id).strip().upper()
    matches = [
        node for node in graph.nodes.values()
        if node.station.upper() == station and node.role in STATION_ROLES
    ]
    if len(matches) != 1:
        raise GraphError(
            f"station '{station}' must have exactly one pickup/dropoff dock node"
        )
    return matches[0]


def update_station(
    graph: FieldGraph,
    station_id: str,
    approach_qr_id: str,
    dock_heading_yaw: float,
    turn_direction: str,
    line_follow_duration_s: float,
) -> NodeData:
    """Atomically replace a station node's approach metadata in memory."""
    node = station_node(graph, station_id)
    metadata = dict(node.metadata)
    metadata.update(checked_values(
        approach_qr_id,
        dock_heading_yaw,
        turn_direction,
        line_follow_duration_s,
    ))
    return graph.upsert_node(replace(node, metadata=metadata))


def config_from_node(node: NodeData) -> dict[str, Any] | None:
    """Read and validate configuration when all required keys are present."""
    keys = (
        "approach_qr_id",
        "dock_heading_yaw",
        "turn_direction",
        "line_follow_duration_s",
    )
    if not any(key in node.metadata for key in keys):
        return None
    if not all(key in node.metadata for key in keys):
        raise GraphError(f"station '{node.station}' approach config is incomplete")
    return checked_values(*(node.metadata[key] for key in keys))
