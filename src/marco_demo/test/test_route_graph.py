import math

import pytest
from geometry_msgs.msg import Pose2D, PoseStamped
from nav_msgs.msg import Path

from marco_demo.demo_scenario_manager import (
    DemoAbort,
    DemoScenarioManager,
    _angle_error,
    _build_route_graph,
    _first_distinct_point_heading,
    _last_path_segment_heading,
    _navigation_only_abort_is_acceptable,
)


class _RouteGoalCaptured(Exception):
    def __init__(self, goal):
        super().__init__("route goal captured")
        self.goal = goal


class _RouteGoalProbe:
    def __init__(self):
        self._route_goal_ids = {"A": 2, "B": 5}
        self._compute_route = object()

    def _wait_obstacle_clear(self):
        return None

    def _run_action_wrapped(self, _client, goal, _label):
        raise _RouteGoalCaptured(goal)


def _point(x: float, y: float) -> Pose2D:
    point = Pose2D()
    point.x = x
    point.y = y
    return point


def _path(*coordinates: tuple[float, float]) -> Path:
    path = Path()
    for x, y in coordinates:
        pose = PoseStamped()
        pose.pose.position.x = x
        pose.pose.position.y = y
        path.poses.append(pose)
    return path


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
    assert all(
        edge["properties"]["metadata"]["abs_speed_limit"] == 0.36
        for edge in edges
    )


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


def test_last_path_segment_heading_uses_geometric_heading():
    heading = _last_path_segment_heading(
        _path((0.0, 0.0), (1.0, 0.0), (1.0, 2.0))
    )

    assert heading == pytest.approx(math.pi / 2.0)


def test_last_path_segment_heading_skips_duplicate_final_poses():
    heading = _last_path_segment_heading(
        _path((0.0, 0.0), (-2.0, 0.0), (-2.0, 0.0))
    )

    assert abs(heading) == pytest.approx(math.pi)


def test_last_path_segment_heading_rejects_zero_length_path():
    with pytest.raises(DemoAbort, match="yon hesaplanabilecek"):
        _last_path_segment_heading(_path((1.0, 1.0), (1.0, 1.0)))


def test_first_distinct_point_heading_skips_origin_duplicate():
    heading = _first_distinct_point_heading(
        _point(1.0, 1.0),
        [_point(1.0, 1.0), _point(2.0, 2.0)],
    )

    assert heading == pytest.approx(math.pi / 4.0)


def test_first_distinct_point_heading_requires_exit_point():
    with pytest.raises(DemoAbort, match="B cikis yonu"):
        _first_distinct_point_heading(
            _point(1.0, 1.0),
            [_point(1.01, 1.0)],
        )


def test_angle_error_handles_pi_wraparound():
    error = _angle_error(math.radians(-179.0), math.radians(179.0))

    assert math.degrees(error) == pytest.approx(2.0)


def test_navigation_only_accepts_small_terminal_abort():
    accepted, position_error, yaw_error = (
        _navigation_only_abort_is_acceptable(
            target_x=2.0,
            target_y=1.0,
            target_yaw=math.radians(-179.0),
            robot_x=1.91,
            robot_y=1.02,
            robot_yaw=math.radians(179.0),
            position_tolerance=0.10,
            yaw_tolerance=math.radians(10.0),
        )
    )

    assert accepted
    assert position_error < 0.10
    assert math.degrees(yaw_error) == pytest.approx(2.0)


@pytest.mark.parametrize(
    ("robot_x", "robot_yaw"),
    (
        (1.80, 0.0),
        (2.0, math.radians(20.0)),
    ),
)
def test_navigation_only_rejects_large_terminal_error(robot_x, robot_yaw):
    accepted, _position_error, _yaw_error = (
        _navigation_only_abort_is_acceptable(
            target_x=2.0,
            target_y=1.0,
            target_yaw=0.0,
            robot_x=robot_x,
            robot_y=1.0,
            robot_yaw=robot_yaw,
            position_tolerance=0.10,
            yaw_tolerance=math.radians(10.0),
        )
    )

    assert not accepted


def test_b_route_can_use_explicit_a_node_as_start():
    probe = _RouteGoalProbe()

    with pytest.raises(_RouteGoalCaptured) as captured:
        DemoScenarioManager._move_nav2_route(
            probe,
            "B",
            _point(6.0, 1.0),
            use_path_heading=True,
            start_name="A",
        )

    goal = captured.value.goal
    assert goal.start_id == 2
    assert goal.goal_id == 5
    assert goal.use_start is True
    assert goal.use_poses is False
