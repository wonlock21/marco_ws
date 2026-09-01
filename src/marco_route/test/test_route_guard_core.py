import json
import math

import pytest

from marco_route.route_guard_core import (
    RouteEdge,
    edge_allowed,
    guard_decision,
    load_route_graph,
    nearest_edge,
    nearest_projection,
)


def edge(**overrides):
    values = {
        "feature_id": 10,
        "logical_id": 1000,
        "start_feature_id": 1,
        "end_feature_id": 2,
        "start_name": "A",
        "end_name": "B",
        "points": ((0.0, 0.0), (2.0, 0.0)),
        "max_speed": 0.20,
        "load_rule": "any",
        "movement_direction": "forward",
        "gate_event": "",
    }
    values.update(overrides)
    return RouteEdge(**values)


def test_projection_uses_nearest_segment_not_nearest_vertex():
    projection = nearest_projection((1.0, 0.3), ((0.0, 0.0), (2.0, 0.0)))
    assert projection.distance == pytest.approx(0.3)
    assert projection.x == pytest.approx(1.0)
    assert projection.segment_ratio == pytest.approx(0.5)


@pytest.mark.parametrize(
    "error,band,limit,stop",
    [
        (0.049, "normal", 0.0, False),
        (0.050, "warning", 0.0, False),
        (0.080, "slowdown", 0.06, False),
        (0.100, "stop", 0.06, True),
    ],
)
def test_guard_bands_are_deterministic(error, band, limit, stop):
    decision = guard_decision(error)
    assert decision.band == band
    assert decision.speed_limit == pytest.approx(limit)
    assert decision.stop is stop


def test_loaded_and_empty_edges_are_filtered_without_changing_any_edges():
    assert edge_allowed(edge(load_rule="empty"), loaded=False)
    assert not edge_allowed(edge(load_rule="empty"), loaded=True)
    assert not edge_allowed(edge(load_rule="loaded"), loaded=False)
    assert edge_allowed(
        edge(load_rule="loaded", movement_direction="reverse"), loaded=True
    )
    assert not edge_allowed(
        edge(load_rule="loaded", movement_direction="forward"), loaded=True
    )
    assert edge_allowed(edge(load_rule="any"), loaded=True)


def test_nearest_semantic_edge_is_reported():
    horizontal = edge()
    vertical = edge(
        feature_id=11,
        logical_id=1001,
        points=((3.0, 0.0), (3.0, 2.0)),
    )
    match = nearest_edge((3.1, 1.0), (horizontal, vertical))
    assert match is not None
    assert match[0].logical_id == 1001
    assert match[1].distance == pytest.approx(0.1)


def test_geojson_loader_keeps_nav2_and_logical_edge_ids(tmp_path):
    document = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"id": 1, "name": "A"},
                "geometry": {"type": "Point", "coordinates": [0, 0]},
            },
            {
                "type": "Feature",
                "properties": {"id": 2, "name": "Q5"},
                "geometry": {"type": "Point", "coordinates": [1, 0]},
            },
            {
                "type": "Feature",
                "properties": {
                    "id": 7,
                    "startid": 1,
                    "endid": 2,
                    "metadata": {
                        "marco_edge_id": 900,
                        "abs_speed_limit": 0.12,
                        "load_rule": "loaded",
                        "movement_direction": "reverse",
                        "gate_event": "q5_enter",
                    },
                },
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": [[[0, 0], [1, 0]]],
                },
            },
        ],
    }
    path = tmp_path / "route.geojson"
    path.write_text(json.dumps(document), encoding="utf-8")
    loaded = load_route_graph(path)
    assert len(loaded.edges) == 1
    loaded_edge = loaded.edges[0]
    assert loaded_edge.feature_id == 7
    assert loaded_edge.logical_id == 900
    assert loaded_edge.end_name == "Q5"
    assert loaded_edge.gate_event == "q5_enter"
    assert math.isclose(loaded_edge.max_speed, 0.12)
