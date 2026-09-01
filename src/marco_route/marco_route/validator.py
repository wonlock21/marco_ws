"""Static validation for field maps and semantic route graphs."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .field_store import FieldStore, StoreError, stations_document
from .graph_model import FieldGraph
from .station_config import config_from_node


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors


def _reachable(graph: FieldGraph, start: int, goal: int) -> bool:
    adjacency: dict[int, set[int]] = {node_id: set() for node_id in graph.nodes}
    for edge in graph.edges.values():
        adjacency.setdefault(edge.start_node_id, set()).add(edge.end_node_id)
        if edge.bidirectional:
            adjacency.setdefault(edge.end_node_id, set()).add(edge.start_node_id)
    pending = [start]
    visited = {start}
    while pending:
        current = pending.pop()
        if current == goal:
            return True
        for candidate in adjacency.get(current, set()) - visited:
            visited.add(candidate)
            pending.append(candidate)
    return False


def _reachable_without(
    graph: FieldGraph, start: int, goal: int, blocked: set[int]
) -> bool:
    if start in blocked or goal in blocked:
        return False
    adjacency: dict[int, set[int]] = {node_id: set() for node_id in graph.nodes}
    for edge in graph.edges.values():
        if edge.start_node_id in blocked or edge.end_node_id in blocked:
            continue
        adjacency[edge.start_node_id].add(edge.end_node_id)
        if edge.bidirectional:
            adjacency[edge.end_node_id].add(edge.start_node_id)
    pending, visited = [start], {start}
    while pending:
        current = pending.pop()
        if current == goal:
            return True
        for candidate in adjacency.get(current, set()) - visited:
            visited.add(candidate)
            pending.append(candidate)
    return False


def _load_pgm(path: Path) -> tuple[int, int, bytes]:
    with path.open("rb") as stream:
        tokens: list[bytes] = []
        while len(tokens) < 4:
            line = stream.readline()
            if not line:
                break
            tokens.extend(line.split(b"#", 1)[0].split())
        if len(tokens) < 4 or tokens[0] != b"P5":
            raise StoreError("map image must be a binary PGM")
        width, height, maximum = map(int, tokens[1:4])
        pixels = stream.read()
    if maximum != 255 or len(pixels) != width * height:
        raise StoreError("map PGM payload is invalid")
    return width, height, pixels


def _footprint(store: FieldStore, field_name: str) -> list[tuple[float, float]]:
    path = store.field_directory(field_name) / "calibration_snapshot.yaml"
    try:
        with path.open("r", encoding="utf-8") as stream:
            content = yaml.safe_load(stream) or {}
        raw = content["vehicle_contract"]["geometry"]["footprint"]
        points = [(float(point[0]), float(point[1])) for point in raw]
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as error:
        raise StoreError(f"vehicle footprint cannot be read: {error}") from error
    if len(points) < 3 or not all(
        math.isfinite(value) for point in points for value in point
    ):
        raise StoreError("vehicle footprint must contain at least three finite points")
    return points


def _validate_edge_clearance(
    store: FieldStore,
    graph: FieldGraph,
    result: ValidationResult,
    footprint_override: list[tuple[float, float]] | None = None,
) -> None:
    field_dir = store.field_directory(graph.field_name)
    config = store.map_config(graph.field_name)
    image = Path(str(config.get("image", "")))
    image = image.resolve() if image.is_absolute() else (field_dir / image).resolve()
    if image.parent != field_dir:
        raise StoreError("map image escapes field directory")
    width, height, pixels = _load_pgm(image)
    resolution = float(config["resolution"])
    origin_x, origin_y, origin_yaw = (float(value) for value in config["origin"])
    cosine, sine = math.cos(origin_yaw), math.sin(origin_yaw)
    footprint = footprint_override or _footprint(store, graph.field_name)
    min_fx = min(point[0] for point in footprint)
    max_fx = max(point[0] for point in footprint)
    min_fy = min(point[1] for point in footprint)
    max_fy = max(point[1] for point in footprint)
    footprint_samples = [
        (fx, fy)
        for fx in (
            min_fx + index * min(resolution, 0.05)
            for index in range(
                int(math.ceil((max_fx - min_fx) / min(resolution, 0.05))) + 1
            )
        )
        for fy in (
            min_fy + index * min(resolution, 0.05)
            for index in range(
                int(math.ceil((max_fy - min_fy) / min(resolution, 0.05))) + 1
            )
        )
    ]
    for edge in graph.edges.values():
        start, end = graph.nodes[edge.start_node_id], graph.nodes[edge.end_node_id]
        length = math.hypot(end.x - start.x, end.y - start.y)
        steps = max(1, int(math.ceil(length / (resolution * 0.5))))
        travel_yaw = math.atan2(end.y - start.y, end.x - start.x)
        if edge.movement_direction == "reverse":
            travel_yaw += math.pi
        route_cosine, route_sine = math.cos(travel_yaw), math.sin(travel_yaw)
        blocked = False
        for index in range(steps + 1):
            ratio = index / steps
            x = start.x + ratio * (end.x - start.x)
            y = start.y + ratio * (end.y - start.y)
            for fx, fy in footprint_samples:
                world_x = x + fx * route_cosine - fy * route_sine
                world_y = y + fx * route_sine + fy * route_cosine
                dx, dy = world_x - origin_x, world_y - origin_y
                local_x = cosine * dx + sine * dy
                local_y = -sine * dx + cosine * dy
                px, py = int(math.floor(local_x / resolution)), int(
                    math.floor(local_y / resolution)
                )
                if (
                    px < 0
                    or py < 0
                    or px >= width
                    or py >= height
                    or pixels[(height - 1 - py) * width + px] < 250
                ):
                    result.errors.append(
                        f"edge {edge.edge_id} vehicle footprint intersects "
                        "occupied/unknown/outside map"
                    )
                    blocked = True
                    break
            if blocked:
                break


def _station_node(graph: FieldGraph, station: str) -> int | None:
    matching = [
        node for node in graph.nodes.values()
        if node.station.casefold() == station.casefold()
    ]
    if not matching:
        return None
    preferred = [
        node for node in matching
        if node.role in ("pickup_dock", "dropoff_dock", "wait")
    ]
    return (preferred or matching)[0].node_id


def validate_field(
    store: FieldStore,
    graph: FieldGraph,
    competition_profile: bool = True,
    footprint: list[tuple[float, float]] | None = None,
) -> ValidationResult:
    result = ValidationResult()
    if not graph.nodes:
        result.errors.append("route graph has no nodes")
    if not graph.edges:
        result.errors.append("route graph has no edges")
    for issue in store.package_issues(graph.field_name):
        result.errors.append(issue)

    try:
        manifest_path = store.field_directory(graph.field_name) / "field.yaml"
        with manifest_path.open("r", encoding="utf-8") as stream:
            manifest = yaml.safe_load(stream) or {}
        if competition_profile and manifest.get("profile") != "competition":
            result.errors.append("production profile rejects demo/test field package")
    except (OSError, AttributeError, yaml.YAMLError) as error:
        result.errors.append(f"field.yaml cannot be read: {error}")

    try:
        if store.read_stations(graph.field_name) != stations_document(graph):
            result.errors.append("stations.yaml does not match route.geojson")
    except StoreError as error:
        result.errors.append(str(error))

    try:
        _validate_edge_clearance(store, graph, result, footprint)
    except StoreError as error:
        result.errors.append(str(error))

    try:
        config = store.map_config(graph.field_name)
        width, height = store.map_dimensions(graph.field_name)
        resolution = float(config["resolution"])
        origin_x, origin_y, origin_yaw = (float(value) for value in config["origin"])
        cosine, sine = math.cos(origin_yaw), math.sin(origin_yaw)
        for node in graph.nodes.values():
            dx, dy = node.x - origin_x, node.y - origin_y
            local_x = cosine * dx + sine * dy
            local_y = -sine * dx + cosine * dy
            inside = (
                0.0 <= local_x < width * resolution
                and 0.0 <= local_y < height * resolution
            )
            if not inside:
                result.errors.append(
                    f"node '{node.name}' ({node.node_id}) is outside the map"
                )
    except StoreError as error:
        result.errors.append(str(error))

    names: dict[str, int] = {}
    for node in graph.nodes.values():
        folded = node.name.casefold()
        if folded in names:
            result.errors.append(
                f"duplicate node name '{node.name}' ({names[folded]}, {node.node_id})"
            )
        names[folded] = node.node_id
        if not math.isfinite(node.yaw):
            result.errors.append(f"node '{node.name}' has no finite yaw")
        if not node.station and node.role != "transit":
            result.errors.append(f"node '{node.name}' has no station")
        if node.role in ("pickup_dock", "dropoff_dock"):
            try:
                config = config_from_node(node)
                if config is None:
                    result.warnings.append(
                        f"station '{node.station}' has no F7A approach configuration"
                    )
                else:
                    expected_role = (
                        "pickup_approach"
                        if node.role == "pickup_dock"
                        else "dropoff_approach"
                    )
                    approach_nodes = [
                        candidate for candidate in graph.nodes.values()
                        if candidate.station == node.station
                        and candidate.role in (expected_role, "qr_trigger")
                    ]
                    preferred = [
                        candidate for candidate in approach_nodes
                        if candidate.role == expected_role
                    ]
                    selected = preferred or approach_nodes
                    if len(selected) != 1:
                        result.errors.append(
                            f"station '{node.station}' must have exactly one "
                            "QR/approach node for F7B"
                        )
                    if config["turn_direction"] == "auto":
                        result.errors.append(
                            f"station '{node.station}' uses turn_direction=auto; "
                            "F7B requires left or right until both costmap arcs "
                            "can be compared"
                        )
            except (ValueError, TypeError) as error:
                result.errors.append(str(error))

    for edge in graph.edges.values():
        if edge.start_node_id not in graph.nodes or edge.end_node_id not in graph.nodes:
            result.errors.append(f"edge {edge.edge_id} references a missing node")
        if edge.load_rule == "loaded":
            if edge.movement_direction != "reverse":
                result.errors.append(
                    f"loaded edge {edge.edge_id} must use reverse movement"
                )
    q5_nodes = {
        node.node_id for node in graph.nodes.values()
        if node.role == "gate_q5"
    }
    if competition_profile and not q5_nodes:
        result.errors.append("required q5 gate node is missing")
    for edge in graph.edges.values():
        if q5_nodes.intersection((edge.start_node_id, edge.end_node_id)):
            if not edge.gate_event:
                result.errors.append(
                    f"q5 edge {edge.edge_id} has no gate event"
                )

    if competition_profile:
        required = ["WAIT", "A1", "A2", "A3", "B1", "B2", "B3"]
        stations = {name: _station_node(graph, name) for name in required}
        for name, node_id in stations.items():
            if node_id is None:
                result.errors.append(f"required station '{name}' is missing")
        if all(node_id is not None for node_id in stations.values()):
            wait_node = graph.nodes[stations["WAIT"]]
            if wait_node.role != "wait":
                result.errors.append("WAIT station must use WAIT role")
            for pickup in ("A1", "A2", "A3"):
                if graph.nodes[stations[pickup]].role != "pickup_dock":
                    result.errors.append(
                        f"{pickup} must include a PICKUP_DOCK station node"
                    )
            for dropoff in ("B1", "B2", "B3"):
                if graph.nodes[stations[dropoff]].role != "dropoff_dock":
                    result.errors.append(
                        f"{dropoff} must include a DROPOFF_DOCK station node"
                    )
            wait = stations["WAIT"]
            for pickup in ("A1", "A2", "A3"):
                if not _reachable(graph, wait, stations[pickup]):
                    result.errors.append(f"WAIT cannot reach {pickup}")
                for dropoff in ("B1", "B2", "B3"):
                    if not _reachable(graph, stations[pickup], stations[dropoff]):
                        result.errors.append(f"{pickup} cannot reach {dropoff}")
                    elif _reachable_without(
                        graph,
                        stations[pickup],
                        stations[dropoff],
                        q5_nodes,
                    ):
                        result.errors.append(
                            f"{pickup}->{dropoff} has an unauthorized q5 bypass"
                        )
            for dropoff in ("B1", "B2", "B3"):
                if not _reachable(graph, stations[dropoff], wait):
                    result.errors.append(f"{dropoff} cannot return to WAIT")
    return result
