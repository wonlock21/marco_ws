import pytest

from marco_route.graph_model import EdgeData, FieldGraph, GraphError, NodeData


def node(node_id, name, role="transit", station=""):
    return NodeData(
        node_id, name, role, station, 1.0 + node_id % 5, 2.0, 0.1
    )


def test_feature_ids_are_unique_uint16_and_logical_ids_roundtrip():
    graph = FieldGraph("field")
    graph.upsert_node(node(2**40, "large"))
    graph.upsert_node(node(7, "small"))
    graph.upsert_edge(EdgeData(
        2**48,
        2**40,
        7,
        bidirectional=True,
        max_speed=0.25,
    ))

    content = graph.to_geojson()
    feature_ids = [
        feature["properties"]["id"] for feature in content["features"]
    ]
    assert feature_ids == [0, 1, 2, 3]
    assert len(feature_ids) == len(set(feature_ids))
    assert all(0 <= feature_id <= 65_535 for feature_id in feature_ids)
    assert all(
        feature["properties"]["startid"] in (0, 1)
        and feature["properties"]["endid"] in (0, 1)
        for feature in content["features"][2:]
    )

    loaded = FieldGraph.from_geojson(content, "field")
    assert loaded == graph


def test_duplicate_feature_id_is_rejected():
    graph = FieldGraph("field")
    graph.upsert_node(node(1, "one"))
    graph.upsert_node(node(2, "two"))
    content = graph.to_geojson()
    content["features"][1]["properties"]["id"] = 0
    with pytest.raises(GraphError, match="duplicate GeoJSON feature id"):
        FieldGraph.from_geojson(content, "field")


@pytest.mark.parametrize("role", ["dock", "", "PICKUP"])
def test_noncanonical_roles_are_rejected(role):
    with pytest.raises(GraphError, match="node role"):
        node(1, "bad", role=role).checked()


@pytest.mark.parametrize("speed", [0.0, 0.049, 0.501, 1.0])
def test_speed_outside_safe_range_is_rejected(speed):
    with pytest.raises(GraphError, match="abs_speed_limit"):
        EdgeData(1, 1, 2, max_speed=speed).checked()


def test_duplicate_node_name_is_case_insensitive():
    graph = FieldGraph("field")
    graph.upsert_node(node(1, "Dock"))
    with pytest.raises(GraphError, match="already exists"):
        graph.upsert_node(node(2, "dock"))


def test_nonfinite_node_yaw_is_rejected():
    invalid = NodeData(1, "bad-yaw", "transit", "", 1.0, 2.0, float("nan"))
    with pytest.raises(GraphError, match="node yaw must be finite"):
        invalid.checked()


def test_nav2_penalty_contains_turn_and_q5_wait_costs():
    graph = FieldGraph("field")
    graph.upsert_node(NodeData(1, "one", "transit", "", 0.0, 0.0, 0.0))
    graph.upsert_node(NodeData(2, "two", "gate_q5", "Q5", 0.0, 1.0, 0.0))
    graph.upsert_edge(EdgeData(
        10,
        1,
        2,
        gate_event="q5_enter",
        metadata={"turn_weight": 2.0, "q5_wait_s": 3.0},
    ))
    feature = graph.to_geojson()["features"][2]
    # 90-degree turn * weight 2 = 1.0, plus 3 seconds q5 wait.
    assert feature["properties"]["metadata"]["planning_penalty"] == pytest.approx(4.0)


def test_invalid_planning_penalty_metadata_is_rejected_on_serialization():
    graph = FieldGraph("field")
    graph.upsert_node(NodeData(1, "one", "transit", "", 0.0, 0.0, 0.0))
    graph.upsert_node(NodeData(2, "two", "transit", "", 1.0, 0.0, 0.0))
    graph.upsert_edge(EdgeData(
        10, 1, 2, metadata={"q5_wait_s": float("nan")}
    ))
    with pytest.raises(GraphError, match="q5_wait_s"):
        graph.to_geojson()
