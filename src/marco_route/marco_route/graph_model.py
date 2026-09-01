"""Canonical semantic graph model and Nav2 GeoJSON conversion."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, replace
from typing import Any


SCHEMA = "marco.field_route"
SCHEMA_VERSION = 2
MIN_FEATURE_ID = 0
MAX_FEATURE_ID = 65_535
MAX_LOGICAL_ID = (1 << 64) - 1

ROLES = frozenset({
    "wait",
    "pickup_approach",
    "pickup_dock",
    "dropoff_approach",
    "dropoff_dock",
    "gate_q5",
    "qr_trigger",
    "transit",
})
LOAD_RULES = frozenset({"any", "empty", "loaded"})
APPROACH_MODES = frozenset({"navigate", "dock", "pass_through", "trigger"})
MOVEMENT_DIRECTIONS = frozenset({"forward", "reverse", "either"})


class GraphError(ValueError):
    """Raised when a graph or semantic entity is malformed."""


def _finite(value: float, label: str) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise GraphError(f"{label} must be finite")
    return value


def _enum(value: str, allowed: frozenset[str], label: str) -> str:
    normalized = str(value).strip().lower()
    if normalized not in allowed:
        expected = ", ".join(sorted(item.upper() for item in allowed))
        raise GraphError(f"{label} must be one of: {expected}")
    return normalized


def parse_metadata(value: str | dict[str, Any] | None) -> dict[str, Any]:
    if value in (None, ""):
        return {}
    if isinstance(value, dict):
        return dict(value)
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError) as error:
        raise GraphError(f"metadata_json is invalid: {error}") from error
    if not isinstance(parsed, dict):
        raise GraphError("metadata_json must contain a JSON object")
    return parsed


@dataclass(frozen=True)
class NodeData:
    node_id: int
    name: str
    role: str
    station: str
    x: float
    y: float
    yaw: float
    load_rule: str = "any"
    approach_mode: str = "navigate"
    metadata: dict[str, Any] = field(default_factory=dict)

    def checked(self) -> "NodeData":
        if not 0 <= int(self.node_id) <= MAX_LOGICAL_ID:
            raise GraphError("node_id must be an unsigned 64-bit integer")
        if not self.name.strip():
            raise GraphError("node name cannot be empty")
        return replace(
            self,
            node_id=int(self.node_id),
            name=self.name.strip(),
            role=_enum(self.role, ROLES, "node role"),
            station=self.station.strip(),
            x=_finite(self.x, "node x"),
            y=_finite(self.y, "node y"),
            yaw=_finite(self.yaw, "node yaw"),
            load_rule=_enum(self.load_rule, LOAD_RULES, "node load_rule"),
            approach_mode=_enum(
                self.approach_mode, APPROACH_MODES, "node approach_mode"
            ),
            metadata=parse_metadata(self.metadata),
        )


@dataclass(frozen=True)
class EdgeData:
    edge_id: int
    start_node_id: int
    end_node_id: int
    bidirectional: bool = False
    cost: float = 1.0
    max_speed: float = 0.20
    load_rule: str = "any"
    movement_direction: str = "forward"
    gate_event: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def checked(self) -> "EdgeData":
        if not 0 <= int(self.edge_id) <= MAX_LOGICAL_ID:
            raise GraphError("edge_id must be an unsigned 64-bit integer")
        if int(self.start_node_id) == int(self.end_node_id):
            raise GraphError("edge endpoints must be different")
        cost = _finite(self.cost, "edge cost")
        speed = _finite(self.max_speed, "edge max_speed")
        if cost <= 0.0:
            raise GraphError("edge cost must be positive")
        if not 0.05 <= speed <= 0.50:
            raise GraphError("edge abs_speed_limit must be between 0.05 and 0.50")
        return replace(
            self,
            edge_id=int(self.edge_id),
            start_node_id=int(self.start_node_id),
            end_node_id=int(self.end_node_id),
            bidirectional=bool(self.bidirectional),
            cost=cost,
            max_speed=speed,
            load_rule=_enum(self.load_rule, LOAD_RULES, "edge load_rule"),
            movement_direction=_enum(
                self.movement_direction,
                MOVEMENT_DIRECTIONS,
                "edge movement_direction",
            ),
            gate_event=self.gate_event.strip(),
            metadata=parse_metadata(self.metadata),
        )


@dataclass
class FieldGraph:
    field_name: str
    nodes: dict[int, NodeData] = field(default_factory=dict)
    edges: dict[int, EdgeData] = field(default_factory=dict)

    def upsert_node(self, node: NodeData) -> NodeData:
        node = node.checked()
        duplicate = next(
            (
                item for item in self.nodes.values()
                if item.node_id != node.node_id
                and item.name.casefold() == node.name.casefold()
            ),
            None,
        )
        if duplicate:
            raise GraphError(f"node name already exists: {duplicate.name}")
        self.nodes[node.node_id] = node
        return node

    def delete_node(self, node_id: int, delete_edges: bool = False) -> int:
        node_id = int(node_id)
        if node_id not in self.nodes:
            raise GraphError(f"node not found: {node_id}")
        connected = [
            edge_id for edge_id, edge in self.edges.items()
            if node_id in (edge.start_node_id, edge.end_node_id)
        ]
        if connected and not delete_edges:
            raise GraphError("node has connected edges")
        for edge_id in connected:
            del self.edges[edge_id]
        del self.nodes[node_id]
        return len(connected)

    def upsert_edge(self, edge: EdgeData) -> EdgeData:
        edge = edge.checked()
        missing = [
            node_id for node_id in (edge.start_node_id, edge.end_node_id)
            if node_id not in self.nodes
        ]
        if missing:
            raise GraphError(f"edge references missing nodes: {missing}")
        self.edges[edge.edge_id] = edge
        return edge

    def delete_edge(self, edge_id: int) -> None:
        edge_id = int(edge_id)
        if edge_id not in self.edges:
            raise GraphError(f"edge not found: {edge_id}")
        del self.edges[edge_id]

    @classmethod
    def from_geojson(cls, content: dict[str, Any], field_name: str) -> "FieldGraph":
        if not isinstance(content, dict) or content.get("type") != "FeatureCollection":
            raise GraphError("route graph must be a GeoJSON FeatureCollection")
        schema = content.get("marco", {})
        if (
            not isinstance(schema, dict)
            or schema.get("schema") != SCHEMA
            or schema.get("version") != SCHEMA_VERSION
        ):
            raise GraphError(
                f"route graph must use {SCHEMA} schema version {SCHEMA_VERSION}"
            )
        graph = cls(field_name=field_name)
        pending: list[tuple[dict[str, Any], dict[str, Any]]] = []
        feature_ids: set[int] = set()
        feature_to_logical_node: dict[int, int] = {}
        for feature in content.get("features", []):
            if not isinstance(feature, dict):
                raise GraphError("GeoJSON feature must be an object")
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            if not isinstance(properties, dict) or not isinstance(geometry, dict):
                raise GraphError("GeoJSON feature properties/geometry are invalid")
            metadata = properties.get("metadata", {})
            metadata = metadata if isinstance(metadata, dict) else {}
            try:
                feature_id = int(properties.get("id"))
            except (TypeError, ValueError) as error:
                raise GraphError("feature id must be an integer") from error
            if not MIN_FEATURE_ID <= feature_id <= MAX_FEATURE_ID:
                raise GraphError("feature id must be within uint16 range")
            if feature_id in feature_ids:
                raise GraphError(f"duplicate GeoJSON feature id: {feature_id}")
            feature_ids.add(feature_id)
            geometry_type = geometry.get("type")
            if geometry_type == "Point":
                if properties.get("frame") != "map":
                    raise GraphError("node frame must be map")
                coordinates = geometry.get("coordinates", [])
                if not isinstance(coordinates, list) or len(coordinates) < 2:
                    raise GraphError("node coordinates are invalid")
                node = NodeData(
                    node_id=metadata.get("marco_node_id", feature_id),
                    name=str(properties.get("name", "")),
                    role=str(metadata.get("role", "")),
                    station=str(
                        metadata.get("station_id", metadata.get("station", ""))
                    ),
                    x=coordinates[0],
                    y=coordinates[1],
                    yaw=metadata.get("yaw"),
                    load_rule=str(metadata.get("load_rule", "any")),
                    approach_mode=str(metadata.get("approach_mode", "navigate")),
                    metadata=metadata.get("custom", {}),
                ).checked()
                if node.node_id in graph.nodes:
                    raise GraphError(f"duplicate logical node id: {node.node_id}")
                graph.upsert_node(node)
                feature_to_logical_node[feature_id] = node.node_id
            elif geometry_type in ("LineString", "MultiLineString"):
                pending.append((properties, metadata))
            else:
                raise GraphError(f"unsupported GeoJSON geometry: {geometry_type}")
        logical_edge_ids: set[int] = set()
        for properties, metadata in pending:
            if metadata.get("synthetic_reverse"):
                continue
            try:
                start_node_id = feature_to_logical_node[int(properties.get("startid"))]
                end_node_id = feature_to_logical_node[int(properties.get("endid"))]
            except (KeyError, TypeError, ValueError) as error:
                raise GraphError("edge references an unknown node feature id") from error
            edge = EdgeData(
                edge_id=metadata.get("marco_edge_id", properties.get("id")),
                start_node_id=start_node_id,
                end_node_id=end_node_id,
                bidirectional=bool(metadata.get("bidirectional", False)),
                cost=properties.get("cost", 1.0),
                max_speed=metadata.get("abs_speed_limit", 0.20),
                load_rule=str(metadata.get("load_rule", "any")),
                movement_direction=str(metadata.get("movement_direction", "forward")),
                gate_event=str(metadata.get("gate_event", "")),
                metadata=metadata.get("custom", {}),
            ).checked()
            if edge.edge_id in logical_edge_ids:
                raise GraphError(f"duplicate logical edge id: {edge.edge_id}")
            logical_edge_ids.add(edge.edge_id)
            graph.upsert_edge(edge)
        return graph

    def to_geojson(self) -> dict[str, Any]:
        features: list[dict[str, Any]] = []
        checked_nodes = [
            node.checked()
            for node in sorted(self.nodes.values(), key=lambda item: item.node_id)
        ]
        checked_edges = [
            edge.checked()
            for edge in sorted(self.edges.values(), key=lambda item: item.edge_id)
        ]
        feature_count = len(checked_nodes) + sum(
            2 if edge.bidirectional else 1 for edge in checked_edges
        )
        if feature_count > MAX_FEATURE_ID + 1:
            raise GraphError("graph exceeds the 65536 Nav2 feature limit")
        node_feature_ids = {
            node.node_id: feature_id
            for feature_id, node in enumerate(checked_nodes)
        }
        next_feature_id = len(checked_nodes)
        for node in checked_nodes:
            feature_id = node_feature_ids[node.node_id]
            node = node.checked()
            features.append({
                "type": "Feature",
                "properties": {
                    "id": feature_id,
                    "frame": "map",
                    "name": node.name,
                    "metadata": {
                        "marco_node_id": node.node_id,
                        "role": node.role,
                        "station_id": node.station,
                        "yaw": node.yaw,
                        "load_rule": node.load_rule,
                        "approach_mode": node.approach_mode,
                        "custom": node.metadata,
                    },
                },
                "geometry": {"type": "Point", "coordinates": [node.x, node.y]},
            })
        for edge in checked_edges:
            start = self.nodes[edge.start_node_id]
            end = self.nodes[edge.end_node_id]
            features.append(self._edge_feature(
                edge,
                start,
                end,
                node_feature_ids,
                next_feature_id,
                False,
            ))
            next_feature_id += 1
            if edge.bidirectional:
                features.append(self._edge_feature(
                    edge,
                    end,
                    start,
                    node_feature_ids,
                    next_feature_id,
                    True,
                ))
                next_feature_id += 1
        return {
            "type": "FeatureCollection",
            "name": self.field_name,
            "crs": {"type": "name", "properties": {"name": "map"}},
            "marco": {"schema": SCHEMA, "version": SCHEMA_VERSION},
            "features": features,
        }

    @staticmethod
    def _edge_feature(
        edge: EdgeData,
        start: NodeData,
        end: NodeData,
        node_feature_ids: dict[int, int],
        feature_id: int,
        reverse: bool,
    ) -> dict[str, Any]:
        travel_yaw = math.atan2(end.y - start.y, end.x - start.x)
        if edge.movement_direction == "reverse":
            travel_yaw += math.pi
        turn_angle = math.atan2(
            math.sin(travel_yaw - start.yaw),
            math.cos(travel_yaw - start.yaw),
        )
        turn_weight = float(edge.metadata.get("turn_weight", 1.0))
        q5_wait_s = float(edge.metadata.get(
            "q5_wait_s", 5.0 if edge.gate_event else 0.0
        ))
        if not math.isfinite(turn_weight) or turn_weight < 0.0:
            raise GraphError("edge metadata turn_weight must be finite and nonnegative")
        if not math.isfinite(q5_wait_s) or q5_wait_s < 0.0:
            raise GraphError("edge metadata q5_wait_s must be finite and nonnegative")
        planning_penalty = turn_weight * abs(turn_angle) / math.pi + q5_wait_s
        metadata = {
            "marco_edge_id": edge.edge_id,
            "bidirectional": edge.bidirectional,
            "synthetic_reverse": reverse,
            "abs_speed_limit": edge.max_speed,
            "load_rule": edge.load_rule,
            "movement_direction": edge.movement_direction,
            "gate_event": edge.gate_event,
            "planning_penalty": planning_penalty,
            "custom": edge.metadata,
        }
        return {
            "type": "Feature",
            "properties": {
                "id": feature_id,
                "startid": node_feature_ids[start.node_id],
                "endid": node_feature_ids[end.node_id],
                "cost": edge.cost,
                "metadata": metadata,
            },
            "geometry": {
                "type": "MultiLineString",
                "coordinates": [[[start.x, start.y], [end.x, end.y]]],
            },
        }
