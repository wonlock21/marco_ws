from geometry_msgs.msg import Pose2D

from marco_demo.demo_scenario_manager import _build_route_graph


def _point(x: float, y: float) -> Pose2D:
    point = Pose2D()
    point.x = x
    point.y = y
    return point


def test_build_route_graph_is_ordered_and_bidirectional():
    graph, goal_ids = _build_route_graph(
        _point(2.0, 1.0),
        _point(5.0, 4.0),
        [_point(0.0, 0.0), _point(2.0, 0.0)],
        [_point(5.0, 1.0)],
    )

    nodes = [
        feature for feature in graph["features"]
        if feature["geometry"]["type"] == "Point"
    ]
    edges = [
        feature for feature in graph["features"]
        if feature["geometry"]["type"] == "MultiLineString"
    ]
    assert goal_ids == {"A": 2, "B": 4}
    assert len(nodes) == 5
    assert len(edges) == 8
    assert [node["properties"]["name"] for node in nodes] == [
        "A_ARA_1", "A_ARA_2", "A", "B_ARA_1", "B"
    ]
    assert edges[0]["properties"]["startid"] == 0
    assert edges[0]["properties"]["endid"] == 1
    assert edges[1]["properties"]["startid"] == 1
    assert edges[1]["properties"]["endid"] == 0


def test_task_point_replaces_duplicate_last_route_point():
    graph, goal_ids = _build_route_graph(
        _point(1.0, 0.0),
        _point(2.0, 0.0),
        [_point(0.0, 0.0), _point(1.0, 0.0)],
        [],
    )

    nodes = [
        feature for feature in graph["features"]
        if feature["geometry"]["type"] == "Point"
    ]
    assert len(nodes) == 3
    assert goal_ids == {"A": 1, "B": 2}
    assert nodes[1]["properties"]["name"] == "A"
