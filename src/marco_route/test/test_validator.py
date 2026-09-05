import math

import pytest
import yaml

from marco_route.coordinates import map_to_pixel, pixel_to_map
from marco_route.graph_model import EdgeData, FieldGraph, NodeData
from marco_route.validator import validate_field


def competition_graph():
    graph = FieldGraph("field")
    specifications = [
        (1, "WAIT", "wait", "WAIT", 1.0, 1.0),
        (2, "A1", "pickup_dock", "A1", 2.0, 2.0),
        (3, "A2", "pickup_dock", "A2", 3.0, 2.0),
        (4, "A3", "pickup_dock", "A3", 4.0, 2.0),
        (5, "B1", "dropoff_dock", "B1", 2.0, 4.0),
        (6, "B2", "dropoff_dock", "B2", 3.0, 4.0),
        (7, "B3", "dropoff_dock", "B3", 4.0, 4.0),
        (8, "q5", "gate_q5", "q5", 3.0, 3.0),
        (9, "q6", "gate_q6", "q6", 3.5, 3.0),
    ]
    for node_id, name, role, station, x, y in specifications:
        graph.upsert_node(NodeData(
            node_id, name, role, station, x, y, 0.0
        ))
    for edge_id, endpoint in enumerate(range(1, 5), start=100):
        graph.upsert_edge(EdgeData(
            edge_id,
            endpoint,
            8,
            bidirectional=True,
            max_speed=0.2,
        ))
    graph.upsert_edge(EdgeData(
        110, 8, 9, max_speed=0.2, gate_event="q5_outbound"
    ))
    graph.upsert_edge(EdgeData(
        111, 9, 8, max_speed=0.2, gate_event="q6_return"
    ))
    for edge_id, endpoint in enumerate(range(5, 8), start=120):
        graph.upsert_edge(EdgeData(
            edge_id,
            endpoint,
            9,
            bidirectional=True,
            max_speed=0.2,
        ))
    return graph


def test_competition_reachability_matrix_passes(field_store):
    graph = competition_graph()
    field_store.save_graph(graph)
    result = validate_field(field_store, graph, competition_profile=True)
    assert result.valid, result.errors


def test_directional_gate_event_and_loaded_reverse_are_required(field_store):
    graph = competition_graph()
    graph.edges[110] = EdgeData(
        110,
        8,
        9,
        max_speed=0.2,
        load_rule="loaded",
        movement_direction="forward",
    ).checked()
    field_store.save_graph(graph)
    result = validate_field(field_store, graph, competition_profile=True)
    assert any("gate_event=q5_outbound" in error for error in result.errors)
    assert any("reverse movement" in error for error in result.errors)


def test_outside_node_and_station_drift_are_rejected(field_store):
    graph = competition_graph()
    field_store.save_graph(graph)
    graph.nodes[2] = NodeData(
        2, "A1", "pickup_dock", "A1", 30.0, 30.0, 0.0
    ).checked()
    result = validate_field(field_store, graph, competition_profile=True)
    assert any("outside the map" in error for error in result.errors)
    assert any("stations.yaml does not match" in error for error in result.errors)


def test_q5_bypass_is_rejected(field_store):
    graph = competition_graph()
    graph.upsert_edge(EdgeData(
        999,
        2,
        5,
        max_speed=0.2,
    ))
    field_store.save_graph(graph)
    result = validate_field(field_store, graph, competition_profile=True)
    assert any("unauthorized q5 bypass" in error for error in result.errors)


def test_q6_return_bypass_is_rejected(field_store):
    graph = competition_graph()
    graph.upsert_edge(EdgeData(
        998,
        5,
        1,
        max_speed=0.2,
    ))
    field_store.save_graph(graph)
    result = validate_field(field_store, graph, competition_profile=True)
    assert any("unauthorized q6 bypass" in error for error in result.errors)


def test_missing_return_gate_is_rejected(field_store):
    graph = competition_graph()
    graph.delete_node(9, delete_edges=True)
    field_store.save_graph(graph)
    result = validate_field(field_store, graph, competition_profile=True)
    assert any("return q6 gate node" in error for error in result.errors)


def test_vehicle_footprint_collision_is_rejected(field_store):
    graph = competition_graph()
    field_store.save_graph(graph)
    map_path = field_store.field_directory("field") / "map.pgm"
    payload = bytearray(map_path.read_bytes())
    payload[-(200 * 80) + 80] = 0
    map_path.write_bytes(payload)
    result = validate_field(field_store, graph, competition_profile=True)
    assert any("vehicle footprint intersects" in error for error in result.errors)


def test_production_profile_rejects_demo_manifest(field_store):
    graph = competition_graph()
    field_store.save_graph(graph)
    manifest = field_store.field_directory("field") / "field.yaml"
    content = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    content["profile"] = "demo"
    manifest.write_text(yaml.safe_dump(content), encoding="utf-8")
    result = validate_field(field_store, graph, competition_profile=True)
    assert any("rejects demo/test" in error for error in result.errors)


@pytest.mark.parametrize("origin_yaw", [0.0, 0.4, -1.2])
def test_pixel_map_conversion_is_inverse(origin_yaw):
    origin = (-2.0, 3.0, origin_yaw)
    pixel = (17.25, 42.75, -0.35)
    mapped = pixel_to_map(*pixel, 100, 80, 0.05, origin)
    restored = map_to_pixel(*mapped[:3], 100, 80, 0.05, origin)
    assert restored[:3] == pytest.approx(pixel)
    assert mapped[3] is True
    assert restored[3] is True
    assert -math.pi <= mapped[2] <= math.pi
