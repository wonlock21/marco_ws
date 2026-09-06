"""F8C geometry-derived junction segmentation and execution tests."""

import math
import time
from types import SimpleNamespace

import pytest
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav_msgs.msg import Odometry, Path
from nav2_msgs.msg import Route, RouteEdge, RouteNode

from marco_mission.mission_manager import JunctionManeuver
from marco_mission.mission_manager import MissionAbort
from marco_mission.mission_manager import MissionManager
from marco_mission.mission_manager import _route_junction_maneuvers
from marco_mission.mission_manager import _split_path_at_junctions


def _path(*coordinates):
    path = Path()
    path.header.frame_id = 'map'
    for x, y in coordinates:
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.orientation.w = 1.0
        path.poses.append(pose)
    return path


def _localized_pose(x, y, yaw):
    pose = PoseWithCovarianceStamped()
    pose.pose.pose.position.x = x
    pose.pose.pose.position.y = y
    pose.pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.pose.orientation.w = math.cos(yaw / 2.0)
    return pose


def _route(*coordinates):
    route = Route()
    for index, (x, y) in enumerate(coordinates, start=1):
        node = RouteNode()
        node.nodeid = index
        node.position.x = x
        node.position.y = y
        route.nodes.append(node)
    for index, (start, end) in enumerate(
        zip(route.nodes, route.nodes[1:]), start=10
    ):
        edge = RouteEdge()
        edge.edgeid = index
        edge.start = start.position
        edge.end = end.position
        route.edges.append(edge)
    return route


def _records(*roles):
    return {
        index: {'id': index, 'name': f'N{index}', 'role': role}
        for index, role in enumerate(roles, start=1)
    }


def test_right_angle_transit_node_creates_geometry_derived_spin():
    route = _route((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))

    maneuvers, final_heading = _route_junction_maneuvers(
        route,
        _records('wait', 'transit', 'wait'),
        {10: 'forward', 11: 'forward'},
        math.radians(60.0),
        math.radians(120.0),
    )

    assert len(maneuvers) == 1
    assert maneuvers[0].node_name == 'N2'
    assert maneuvers[0].turn_angle == pytest.approx(math.pi / 2.0)
    assert final_heading == pytest.approx(math.pi / 2.0)


def test_straight_transit_node_does_not_create_spin():
    route = _route((0.0, 0.0), (1.0, 0.0), (2.0, 0.0))

    maneuvers, final_heading = _route_junction_maneuvers(
        route,
        _records('wait', 'transit', 'wait'),
        {10: 'forward', 11: 'forward'},
        math.radians(60.0),
        math.radians(120.0),
    )

    assert maneuvers == []
    assert final_heading == pytest.approx(0.0)


def test_non_transit_qr_or_station_node_never_creates_junction_spin():
    route = _route((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))

    maneuvers, _final_heading = _route_junction_maneuvers(
        route,
        _records('wait', 'pickup_approach', 'pickup_dock'),
        {10: 'forward', 11: 'forward'},
        math.radians(60.0),
        math.radians(120.0),
    )

    assert maneuvers == []


def test_path_is_split_at_the_ordered_junction_pose():
    path = _path((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))
    maneuver = JunctionManeuver(
        node_id=2,
        node_name='D1',
        x=1.0,
        y=0.0,
        incoming_heading=0.0,
        outgoing_heading=math.pi / 2.0,
        turn_angle=math.pi / 2.0,
    )

    segments = _split_path_at_junctions(path, [maneuver], 0.05)

    assert len(segments) == 2
    assert [(p.pose.position.x, p.pose.position.y)
            for p in segments[0].poses] == [(0.0, 0.0), (1.0, 0.0)]
    assert [(p.pose.position.x, p.pose.position.y)
            for p in segments[1].poses] == [(1.0, 0.0), (1.0, 1.0)]


def test_junction_spin_works_in_encoder_only_profile_and_stops_after_spin():
    manager = MissionManager.__new__(MissionManager)
    manager._pose = _localized_pose(1.0, 0.0, 0.0)
    manager._encoder_yaw = 0.0
    manager._filtered_yaw = 0.0
    manager._filtered_odom_seen = time.monotonic()
    manager._odom_freshness = 1.0
    manager._imu_enabled = False
    manager._imu_seen = 0.0
    manager._spin = object()
    manager._obstacle = False
    manager._status_detail = ''
    manager._localization_health = lambda: SimpleNamespace(valid=True)
    parameters = {
        'junction_turn_timeout_s': 20.0,
        'junction_turn_yaw_tolerance_deg': 5.0,
    }
    manager.get_parameter = lambda name: SimpleNamespace(
        value=parameters[name]
    )
    operations = []
    events = []

    def action(_client, goal, _label, _timeout, require_turn_sensors=False):
        operations.append(('spin', goal.target_yaw, require_turn_sensors))
        manager._pose = _localized_pose(1.0, 0.0, math.pi / 2.0)
        manager._encoder_yaw = math.pi / 2.0
        manager._filtered_yaw = math.pi / 2.0
        manager._filtered_odom_seen = time.monotonic()

    manager._action = action
    manager._wait_until_stopped = lambda _label: operations.append(
        ('stop', None, None)
    )
    manager._event = lambda event, **fields: events.append((event, fields))
    maneuver = JunctionManeuver(
        node_id=2,
        node_name='D1',
        x=1.0,
        y=0.0,
        incoming_heading=0.0,
        outgoing_heading=math.pi / 2.0,
        turn_angle=math.pi / 2.0,
    )

    manager._turn_at_junction(maneuver)

    assert operations[0][0] == 'spin'
    assert operations[0][1] == pytest.approx(math.pi / 2.0)
    assert operations[0][2] is True
    assert operations[1] == ('stop', None, None)
    assert events[-1][0] == 'junction_turn_completed'
    assert events[-1][1]['turn_source'] == 'encoder'
    assert events[-1][1]['correction_applied'] is False


def _junction_correction_probe(correct_after_retry):
    manager = MissionManager.__new__(MissionManager)
    manager._pose = _localized_pose(1.0, 0.0, 0.0)
    manager._encoder_yaw = 0.0
    manager._filtered_yaw = 0.0
    manager._filtered_odom_seen = time.monotonic()
    manager._odom_freshness = 1.0
    manager._imu_enabled = False
    manager._imu_seen = 0.0
    manager._spin = object()
    manager._obstacle = False
    manager._status_detail = ''
    manager._localization_health = lambda: SimpleNamespace(valid=True)
    parameters = {
        'junction_turn_timeout_s': 20.0,
        'junction_turn_yaw_tolerance_deg': 5.0,
    }
    manager.get_parameter = lambda name: SimpleNamespace(
        value=parameters[name]
    )
    operations = []
    events = []

    def action(_client, goal, _label, _timeout, require_turn_sensors=False):
        operations.append(('spin', goal.target_yaw, require_turn_sensors))
        # Main Spin stops ten degrees short in the absolute map frame.
        manager._pose = _localized_pose(1.0, 0.0, math.radians(80.0))
        manager._encoder_yaw = math.radians(80.0)
        manager._filtered_yaw = math.radians(80.0)
        manager._filtered_odom_seen = time.monotonic()

    def correction(node_name, correction_turn, correction_source):
        operations.append((
            'correction', node_name, correction_turn, correction_source))
        if correct_after_retry:
            manager._pose = _localized_pose(1.0, 0.0, math.pi / 2.0)
            manager._encoder_yaw = math.pi / 2.0
            manager._filtered_yaw = math.pi / 2.0
            manager._filtered_odom_seen = time.monotonic()

    manager._action = action
    manager._run_junction_turn_correction = correction
    manager._wait_until_stopped = lambda _label: operations.append(
        ('stop', None, None)
    )
    manager._event = lambda event, **fields: events.append((event, fields))
    maneuver = JunctionManeuver(
        node_id=2,
        node_name='D1',
        x=1.0,
        y=0.0,
        incoming_heading=0.0,
        outgoing_heading=math.pi / 2.0,
        turn_angle=math.pi / 2.0,
    )
    return manager, maneuver, operations, events


def test_junction_spin_corrects_map_heading_once_then_continues():
    manager, maneuver, operations, events = _junction_correction_probe(True)

    manager._turn_at_junction(maneuver)

    corrections = [item for item in operations if item[0] == 'correction']
    assert len(corrections) == 1
    assert corrections[0][1] == 'D1'
    assert math.degrees(corrections[0][2]) == pytest.approx(10.0)
    assert corrections[0][3] == 'map'
    assert events[-1][0] == 'junction_turn_completed'
    assert events[-1][1]['correction_applied'] is True
    assert events[-1][1]['fused_turn_error_rad'] == pytest.approx(0.0)


def test_junction_spin_aborts_after_one_unsuccessful_map_correction():
    manager, maneuver, operations, _events = _junction_correction_probe(False)

    with pytest.raises(
        MissionAbort, match='junction yon hatasi 10.00 derece'
    ):
        manager._turn_at_junction(maneuver)

    assert len([
        item for item in operations if item[0] == 'correction'
    ]) == 1


def test_encoder_turn_difference_is_telemetry_when_map_heading_is_correct():
    manager, maneuver, operations, events = _junction_correction_probe(True)

    def action(_client, goal, _label, _timeout, require_turn_sensors=False):
        operations.append(('spin', goal.target_yaw, require_turn_sensors))
        manager._pose = _localized_pose(1.0, 0.0, math.pi / 2.0)
        manager._encoder_yaw = math.radians(100.0)
        manager._filtered_yaw = math.radians(100.0)

    manager._action = action

    manager._turn_at_junction(maneuver)

    assert not [item for item in operations if item[0] == 'correction']
    assert events[-1][0] == 'junction_turn_completed'
    assert events[-1][1]['yaw_error_rad'] == pytest.approx(0.0)
    assert math.degrees(
        events[-1][1]['encoder_turn_error_rad']
    ) == pytest.approx(10.0)


def test_correction_speed_slows_down_near_target():
    speed = MissionManager._junction_correction_speed

    assert speed(math.radians(15.0), 0.25, 0.16, math.radians(10.0)) \
        == pytest.approx(0.25)
    assert speed(math.radians(7.0), 0.25, 0.16, math.radians(10.0)) \
        == pytest.approx(0.175)
    assert speed(math.radians(3.0), 0.25, 0.16, math.radians(10.0)) \
        == pytest.approx(0.16)


def test_raw_and_filtered_odometry_callbacks_remain_separate():
    manager = MissionManager.__new__(MissionManager)
    raw = Odometry()
    raw.pose.pose.orientation.z = math.sin(0.4 / 2.0)
    raw.pose.pose.orientation.w = math.cos(0.4 / 2.0)
    raw.twist.twist.linear.x = 0.12
    raw.twist.twist.angular.z = 0.23
    filtered = Odometry()
    filtered.pose.pose.orientation.z = math.sin(0.9 / 2.0)
    filtered.pose.pose.orientation.w = math.cos(0.9 / 2.0)
    filtered.twist.twist.linear.x = 9.0
    filtered.twist.twist.angular.z = 8.0

    manager._on_odom(raw)
    raw_seen = manager._odom_seen
    manager._on_filtered_odom(filtered)

    assert manager._encoder_yaw == pytest.approx(0.4)
    assert manager._filtered_yaw == pytest.approx(0.9)
    assert manager._linear_speed == pytest.approx(0.12)
    assert manager._angular_speed == pytest.approx(0.23)
    assert manager._odom_seen == raw_seen
    assert manager._filtered_odom_seen > 0.0


def test_junction_correction_uses_raw_yaw_and_decreasing_speed():
    manager = MissionManager.__new__(MissionManager)
    manager._encoder_yaw = 0.0
    manager._filtered_yaw = math.radians(-45.0)
    manager._obstacle = False
    manager._status_detail = ''
    manager._check_abort = lambda: None
    manager._check_action_health = lambda require_turn_sensors: None
    manager._wait_until_stopped = lambda _label: None
    parameters = {
        'junction_turn_correction_angular_speed': 0.25,
        'junction_turn_correction_min_angular_speed': 0.16,
        'junction_turn_correction_timeout_s': 5.0,
        'junction_turn_correction_slowdown_angle_deg': 10.0,
        'junction_turn_correction_stop_margin_deg': 2.5,
        'junction_turn_correction_max_angle_deg': 20.0,
    }
    manager.get_parameter = lambda name: SimpleNamespace(
        value=parameters[name]
    )
    commands = []
    events = []
    manager._event = lambda event, **fields: events.append((event, fields))

    class _Publisher:
        def publish(self, command):
            commands.append(float(command.angular.z))
            if abs(command.angular.z) > 0.0:
                manager._encoder_yaw = MissionManager._wrap_angle(
                    manager._encoder_yaw + math.radians(3.0)
                )

    manager._junction_correction_pub = _Publisher()

    manager._run_junction_turn_correction('D3', math.radians(10.0), 'map')

    moving = [value for value in commands if value > 0.0]
    assert moving == pytest.approx([0.25, 0.175, 0.16])
    assert commands[-1] == pytest.approx(0.0)
    assert manager._filtered_yaw == pytest.approx(math.radians(-45.0))
    assert events[-1][0] == 'junction_turn_correction_finished'
    assert events[-1][1]['odometry_source'] == '/odom'
    assert math.degrees(events[-1][1]['measured_turn_rad']) \
        == pytest.approx(9.0)


class _ExecutionProbe:
    _unique_graph_nodes = MissionManager._unique_graph_nodes

    def __init__(self, fail_on_spin=False, fail_on_first_follow=False):
        self._compute_route = object()
        self._follow_path = object()
        self._route = _route((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))
        self._path = _path((0.0, 0.0), (1.0, 0.0), (1.0, 1.0))
        self._nodes = {
            'START': {'id': 1, 'name': 'START', 'role': 'wait'},
            'D1': {'id': 2, 'name': 'D1', 'role': 'transit'},
            'TARGET': {'id': 3, 'name': 'TARGET', 'role': 'wait'},
        }
        self._edge_directions = {10: 'forward', 11: 'forward'}
        self._current_node = 'START'
        self._edge = ''
        self._pose = None
        self.fail_on_spin = fail_on_spin
        self.fail_on_first_follow = fail_on_first_follow
        self.operations = []
        self.events = []

    def _await_route_constraints(self):
        return None

    def _set_state(self, _state, _target):
        return None

    def _action(self, client, goal, _label):
        if client is self._compute_route:
            return SimpleNamespace(path=self._path, route=self._route)
        self.operations.append(('follow', len(goal.path.poses)))
        if self.fail_on_first_follow and len([
            item for item in self.operations if item[0] == 'follow'
        ]) == 1:
            raise MissionAbort('injected FollowPath failure')
        return SimpleNamespace()

    def _wait_until_stopped(self, _label):
        self.operations.append(('stop', None))

    def _turn_at_junction(self, maneuver):
        self.operations.append(('spin', maneuver.node_name))
        if self.fail_on_spin:
            raise MissionAbort('injected Spin failure')
        # The production helper performs its own post-Spin zero-speed wait.
        self.operations.append(('stop', None))

    def get_parameter(self, name):
        values = {
            'junction_turn_min_angle_deg': 60.0,
            'junction_turn_max_angle_deg': 120.0,
            'junction_path_match_tolerance_m': 0.05,
            'route_terminal_position_tolerance_m': 0.075,
            'route_terminal_yaw_tolerance_deg': 10.0,
        }
        return SimpleNamespace(value=values[name])

    def _event(self, event, **fields):
        self.events.append((event, fields))


def test_navigation_executes_atomic_follow_stop_spin_stop_follow_order():
    probe = _ExecutionProbe()

    MissionManager._navigate(probe, 'TARGET', loaded=False)

    assert probe.operations == [
        ('follow', 2),
        ('stop', None),
        ('spin', 'D1'),
        ('stop', None),
        ('follow', 2),
    ]
    assert probe._current_node == 'TARGET'


def test_spin_failure_prevents_the_next_follow_segment():
    probe = _ExecutionProbe(fail_on_spin=True)

    with pytest.raises(MissionAbort, match='injected Spin failure'):
        MissionManager._navigate(probe, 'TARGET', loaded=False)

    assert probe.operations == [
        ('follow', 2),
        ('stop', None),
        ('spin', 'D1'),
    ]


def test_follow_failure_prevents_stop_spin_and_next_segment():
    probe = _ExecutionProbe(fail_on_first_follow=True)

    with pytest.raises(MissionAbort, match='injected FollowPath failure'):
        MissionManager._navigate(probe, 'TARGET', loaded=False)

    assert probe.operations == [('follow', 2)]
