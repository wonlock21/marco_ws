"""Pure geometry and policy helpers for semantic route protection."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class Projection:
    distance: float
    x: float
    y: float
    segment_index: int
    segment_ratio: float


@dataclass(frozen=True)
class GuardDecision:
    band: str
    speed_limit: float
    stop: bool
    reason: str


@dataclass(frozen=True)
class RouteEdge:
    feature_id: int
    logical_id: int
    start_feature_id: int
    end_feature_id: int
    start_name: str
    end_name: str
    points: tuple[tuple[float, float], ...]
    max_speed: float
    load_rule: str
    movement_direction: str
    gate_event: str


@dataclass(frozen=True)
class RouteGraph:
    edges: tuple[RouteEdge, ...]


def nearest_projection(
    point: tuple[float, float],
    polyline: Sequence[tuple[float, float]],
) -> Projection:
    """Project a point to the nearest finite segment of a polyline."""
    if len(polyline) < 2:
        raise ValueError("polyline must contain at least two points")
    px, py = (float(point[0]), float(point[1]))
    if not math.isfinite(px) or not math.isfinite(py):
        raise ValueError("point must be finite")
    best: Projection | None = None
    for index, (first, second) in enumerate(zip(polyline, polyline[1:])):
        ax, ay = float(first[0]), float(first[1])
        bx, by = float(second[0]), float(second[1])
        dx, dy = bx - ax, by - ay
        denominator = dx * dx + dy * dy
        ratio = 0.0 if denominator <= 1.0e-12 else (
            (px - ax) * dx + (py - ay) * dy
        ) / denominator
        ratio = min(1.0, max(0.0, ratio))
        x, y = ax + ratio * dx, ay + ratio * dy
        distance = math.hypot(px - x, py - y)
        candidate = Projection(distance, x, y, index, ratio)
        if best is None or candidate.distance < best.distance:
            best = candidate
    assert best is not None
    return best


def guard_decision(
    error: float,
    warning_threshold: float = 0.05,
    slowdown_threshold: float = 0.08,
    stop_threshold: float = 0.10,
    slowdown_speed: float = 0.06,
) -> GuardDecision:
    """Return the deterministic 5/8/10 cm route-deviation policy."""
    values = (
        float(error), float(warning_threshold), float(slowdown_threshold),
        float(stop_threshold), float(slowdown_speed),
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError("route guard values must be finite")
    error, warning_threshold, slowdown_threshold, stop_threshold, slowdown_speed = values
    if error < 0.0:
        raise ValueError("cross-track error cannot be negative")
    if not 0.0 < warning_threshold < slowdown_threshold < stop_threshold:
        raise ValueError("thresholds must satisfy 0 < warning < slowdown < stop")
    if slowdown_speed <= 0.0:
        raise ValueError("slowdown speed must be positive")
    if error >= stop_threshold:
        return GuardDecision(
            "stop", slowdown_speed, True,
            f"route_deviation_{error:.3f}m_exceeds_{stop_threshold:.3f}m",
        )
    if error >= slowdown_threshold:
        return GuardDecision("slowdown", slowdown_speed, False, "")
    if error >= warning_threshold:
        return GuardDecision("warning", 0.0, False, "")
    return GuardDecision("normal", 0.0, False, "")


def edge_allowed(edge: RouteEdge, loaded: bool) -> bool:
    """Apply runtime load rules; directionality itself is encoded by the graph."""
    if loaded:
        return edge.load_rule != "empty" and not (
            edge.load_rule == "loaded" and edge.movement_direction != "reverse"
        )
    return edge.load_rule != "loaded"


def nearest_edge(
    point: tuple[float, float], edges: Iterable[RouteEdge]
) -> tuple[RouteEdge, Projection] | None:
    best: tuple[RouteEdge, Projection] | None = None
    for edge in edges:
        projection = nearest_projection(point, edge.points)
        if best is None or projection.distance < best[1].distance:
            best = edge, projection
    return best


def _metadata(properties: dict[str, Any]) -> dict[str, Any]:
    value = properties.get("metadata", {})
    return value if isinstance(value, dict) else {}


def load_route_graph(path: str | Path) -> RouteGraph:
    """Load the Nav2 feature IDs and MarCO semantic edge metadata."""
    with Path(path).open("r", encoding="utf-8") as stream:
        document = json.load(stream)
    if document.get("type") != "FeatureCollection":
        raise ValueError("route graph must be a GeoJSON FeatureCollection")
    names: dict[int, str] = {}
    edge_features: list[dict[str, Any]] = []
    for feature in document.get("features", []):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        feature_id = int(properties["id"])
        if not 0 <= feature_id <= 65_535:
            raise ValueError("Nav2 feature id must fit uint16")
        if geometry.get("type") == "Point":
            names[feature_id] = str(properties.get("name", feature_id))
        elif geometry.get("type") in ("LineString", "MultiLineString"):
            edge_features.append(feature)
    edges: list[RouteEdge] = []
    for feature in edge_features:
        properties = feature["properties"]
        geometry = feature["geometry"]
        metadata = _metadata(properties)
        coordinates = geometry.get("coordinates", [])
        if geometry.get("type") == "MultiLineString":
            if len(coordinates) != 1:
                raise ValueError("route edge MultiLineString must contain one line")
            coordinates = coordinates[0]
        points = tuple((float(item[0]), float(item[1])) for item in coordinates)
        if len(points) < 2 or not all(
            math.isfinite(value) for item in points for value in item
        ):
            raise ValueError("route edge coordinates are invalid")
        start_id, end_id = int(properties["startid"]), int(properties["endid"])
        if start_id not in names or end_id not in names:
            raise ValueError("route edge references a missing node feature")
        feature_id = int(properties["id"])
        edges.append(RouteEdge(
            feature_id=feature_id,
            logical_id=int(metadata.get("marco_edge_id", feature_id)),
            start_feature_id=start_id,
            end_feature_id=end_id,
            start_name=names[start_id],
            end_name=names[end_id],
            points=points,
            max_speed=float(metadata.get("abs_speed_limit", 0.20)),
            load_rule=str(metadata.get("load_rule", "any")).strip().lower(),
            movement_direction=str(
                metadata.get("movement_direction", "forward")
            ).strip().lower(),
            gate_event=str(metadata.get("gate_event", "")).strip(),
        ))
    if not edges:
        raise ValueError("route graph has no edges")
    return RouteGraph(tuple(edges))
