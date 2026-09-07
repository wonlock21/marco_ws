"""Validation and projection for station approach configuration."""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from .graph_model import FieldGraph, GraphError, NodeData


STATION_ROLES = frozenset({"pickup_dock", "dropoff_dock"})


def checked_values(
    approach_qr_id: str,
    line_follow_duration_s: float,
) -> dict[str, Any]:
    """Return a normalized, safe station configuration."""
    qr_id = str(approach_qr_id).strip()
    duration = float(line_follow_duration_s)
    if not qr_id:
        raise GraphError("approach_qr_id cannot be empty")
    if len(qr_id) > 64:
        raise GraphError("approach_qr_id cannot exceed 64 characters")
    if not math.isfinite(duration) or not 0.1 <= duration <= 120.0:
        raise GraphError("line_follow_duration_s must be between 0.1 and 120.0")
    return {
        "approach_qr_id": qr_id,
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
    """Atomically replace editable station approach metadata in memory.

    ``dock_heading_yaw`` and ``turn_direction`` remain in the ROS request for
    wire compatibility, but are intentionally ignored. Heading comes from the
    route geometry and direction is selected from the live local costmap.
    """
    del dock_heading_yaw, turn_direction
    node = station_node(graph, station_id)
    metadata = dict(node.metadata)
    metadata.pop("dock_heading_yaw", None)
    metadata.pop("turn_direction", None)
    metadata.update(checked_values(
        approach_qr_id,
        line_follow_duration_s,
    ))
    return graph.upsert_node(replace(node, metadata=metadata))


def config_from_node(node: NodeData) -> dict[str, Any] | None:
    """Read and validate configuration when all required keys are present."""
    keys = (
        "approach_qr_id",
        "line_follow_duration_s",
    )
    known_keys = keys + ("dock_heading_yaw", "turn_direction")
    if not any(key in node.metadata for key in known_keys):
        return None
    if not all(key in node.metadata for key in keys):
        raise GraphError(f"station '{node.station}' approach config is incomplete")
    return checked_values(*(node.metadata[key] for key in keys))


def derived_dock_heading(graph: FieldGraph, station_id: str) -> float:
    """Derive read-only dock body yaw from the station's upstream edge.

    Runtime mission execution uses the actual ComputeRoute final edge. This
    graph helper exists only for configuration/debug presentation and selects
    the unique edge entering the approach node from outside the dock pair.
    """
    dock = station_node(graph, station_id)
    expected_role = (
        "pickup_approach"
        if dock.role == "pickup_dock"
        else "dropoff_approach"
    )
    candidates = [
        node for node in graph.nodes.values()
        if node.station.upper() == dock.station.upper()
        and node.role in (expected_role, "qr_trigger")
    ]
    preferred = [node for node in candidates if node.role == expected_role]
    selected = preferred or candidates
    if len(selected) != 1:
        raise GraphError(
            f"station '{dock.station}' must have exactly one approach node"
        )
    approach = selected[0]

    headings: list[float] = []
    for edge in graph.edges.values():
        other = None
        if edge.end_node_id == approach.node_id:
            other = graph.nodes[edge.start_node_id]
        elif edge.start_node_id == approach.node_id and edge.bidirectional:
            other = graph.nodes[edge.end_node_id]
        if other is None or other.node_id == dock.node_id:
            continue
        heading = math.atan2(approach.y - other.y, approach.x - other.x)
        if edge.movement_direction == "reverse":
            heading += math.pi
        headings.append(math.atan2(math.sin(heading), math.cos(heading)))

    if len(headings) != 1:
        raise GraphError(
            f"station '{dock.station}' approach node must have exactly one "
            "upstream route edge for debug heading"
        )
    return math.atan2(
        math.sin(headings[0] + math.pi),
        math.cos(headings[0] + math.pi),
    )
