"""Geometry-derived station turn and bounded recovery tests."""

import math
import threading
import time
from types import SimpleNamespace

import pytest
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import (
    Point32,
    PolygonStamped,
    PoseWithCovarianceStamped,
    TransformStamped,
)
from nav2_msgs.msg import Costmap

from marco_mission.mission_manager import MissionAbort
from marco_mission.mission_manager import MissionActionFailure
from marco_mission.mission_manager import MissionManager
from marco_mission.mission_manager import _evaluate_turn_arc


def _station_manager(
    yaw_samples,
    failed_action_calls=(),
    *,
    station='A3',
    approach_xy=(0.0, 0.0),
    dock_xy=(1.0, 0.0),
    turn_direction='right',
    main_measured_turn=None,
    correction_measured_scale=1.0,
):
    manager = MissionManager.__new__(MissionManager)
    manager._nodes = {
        station: {
            'id': 1,
            'name': station,
            'role': 'pickup_dock',
            'station_id': station,
            'xy': list(dock_xy),
            # A legacy persisted value must have no effect on runtime target.
            'dock_heading_yaw': 0.25,
            'turn_direction': 'left',
        },
        f'{station}_yaklasma': {
            'id': 2,
            'name': f'{station}_yaklasma',
            'role': 'pickup_approach',
            'station_id': station,
            'xy': list(approach_xy),
        },
    }
    manager._station_phase = manager._STATION_APPROACHING
    manager._spin = object()
    manager._obstacle = False
    manager._imu_enabled = False
    manager._encoder_yaw = 0.0
    manager._filtered_yaw = 0.0
    manager._status_detail = ''
    manager._check_action_health = lambda require_turn_sensors=False: None
    manager._select_station_turn_direction = (
        lambda _station, _current, _target: turn_direction
    )
    samples = iter(yaw_samples)
    manager._fresh_map_base_yaw = lambda _label: next(samples)
    parameters = {
        'station_turn_timeout_s': 30.0,
        'station_turn_yaw_tolerance_deg': 3.0,
        'station_turn_min_angle_deg': 150.0,
        'station_turn_max_angle_deg': 210.0,
        'station_turn_max_correction_attempts': 5,
        'station_turn_correction_total_timeout_s': 30.0,
    }
    manager.get_parameter = lambda name: SimpleNamespace(
        value=parameters[name]
    )
    manager.operations = []
    manager.events = []
    failed = set(failed_action_calls)
    manager.action_calls = 0

    def action(
        _client, goal, label, _timeout, require_turn_sensors=False
    ):
        manager.action_calls += 1
        manager.operations.append((
            label, goal.target_yaw, require_turn_sensors
        ))
        measured = (
            goal.target_yaw
            if main_measured_turn is None
            else main_measured_turn
        )
        manager._encoder_yaw = MissionManager._wrap_angle(
            manager._encoder_yaw + measured
        )
        manager._filtered_yaw = MissionManager._wrap_angle(
            manager._filtered_yaw + measured
        )
        if manager.action_calls in failed:
            raise MissionActionFailure(label, GoalStatus.STATUS_ABORTED)

    def precise_correction(
        target_name, correction_turn, correction_kind, timeout_limit_s=None
    ):
        manager.operations.append((
            f'{correction_kind}_turn_correction:{target_name}',
            correction_turn,
            timeout_limit_s,
        ))
        measured = correction_turn * correction_measured_scale
        manager._encoder_yaw = MissionManager._wrap_angle(
            manager._encoder_yaw + measured
        )
        manager._filtered_yaw = MissionManager._wrap_angle(
            manager._filtered_yaw + measured
        )
        return measured

    manager._action = action
    manager._run_precise_turn_correction = precise_correction
    manager._wait_until_stopped = lambda label: manager.events.append(
        ('stopped', {'label': label})
    )
    manager._event = lambda name, **fields: manager.events.append(
        (name, fields)
    )
    return manager


def test_station_target_is_dock_geometry_plus_pi_and_uses_auto_direction():
    dock_path_heading = math.radians(30.0)
    target_heading = math.radians(-150.0)
    manager = _station_manager([
        dock_path_heading,
        math.radians(-149.0),
    ], dock_xy=(math.cos(dock_path_heading), math.sin(dock_path_heading)))

    manager._turn_at_station('A3')

    assert len(manager.operations) == 1
    assert manager.operations[0][0] == 'station_turn:A3'
    assert manager.operations[0][1] == pytest.approx(-math.pi)
    completed = next(
        fields for event, fields in manager.events
        if event == 'station_turn_completed'
    )
    assert completed['target_yaw'] == pytest.approx(target_heading)
    assert completed['correction_attempts'] == 0
    assert manager._station_phase == manager._STATION_LINE_FOLLOW_READY


def test_a2_target_uses_graph_geometry_and_fresh_tf_not_route_or_robot_xy():
    approach_xy = (4.077, -2.498)
    dock_xy = (5.322, -2.529)
    dock_path_heading = math.atan2(
        dock_xy[1] - approach_xy[1],
        dock_xy[0] - approach_xy[0],
    )
    target_heading = MissionManager._wrap_angle(
        dock_path_heading + math.pi
    )
    current_tf_yaw = math.radians(15.0)
    previous_route_edge_heading = math.radians(9.68)
    manager = _station_manager(
        [current_tf_yaw, target_heading],
        station='A2',
        approach_xy=approach_xy,
        dock_xy=dock_xy,
        turn_direction='left',
    )
    # Cached robot position intentionally differs from the persisted approach
    # point. Station target geometry must not use this live x/y value.
    manager._pose = PoseWithCovarianceStamped()
    manager._pose.pose.pose.position.x = approach_xy[0] + 0.06
    manager._pose.pose.pose.position.y = approach_xy[1] - 0.04

    manager._turn_at_station('A2')

    assert math.degrees(dock_path_heading) == pytest.approx(-1.426, abs=0.01)
    assert math.degrees(target_heading) == pytest.approx(178.574, abs=0.01)
    assert target_heading != pytest.approx(MissionManager._wrap_angle(
        previous_route_edge_heading + math.pi
    ))
    assert manager.operations[0][0] == 'station_turn:A2'
    assert manager.operations[0][1] == pytest.approx(
        MissionManager._wrap_angle(target_heading - current_tf_yaw)
    )
    heading_event = next(
        fields for event, fields in manager.events
        if event == 'station_dock_heading'
    )
    assert heading_event['station_id'] == 'A2'
    assert heading_event['approach_node'] == 'A2_yaklasma'
    assert heading_event['dock_node'] == 'A2'
    assert heading_event['dock_path_yaw_deg'] == pytest.approx(
        -1.426, abs=0.01
    )
    assert heading_event['target_body_yaw_deg'] == pytest.approx(
        178.574, abs=0.01
    )
    assert heading_event['current_tf_yaw_deg'] == pytest.approx(15.0)
    assert heading_event['turn_command_deg'] == pytest.approx(163.574, abs=0.01)


def _costmap_with_obstacle(x=None, y=None):
    costmap = Costmap()
    costmap.header.frame_id = 'odom'
    costmap.metadata.resolution = 0.05
    costmap.metadata.size_x = 100
    costmap.metadata.size_y = 100
    costmap.metadata.origin.position.x = -2.5
    costmap.metadata.origin.position.y = -2.5
    costmap.metadata.origin.orientation.w = 1.0
    costmap.data = [0] * 10_000
    if x is not None and y is not None:
        cell_x = math.floor((x + 2.5) / 0.05)
        cell_y = math.floor((y + 2.5) / 0.05)
        costmap.data[cell_y * 100 + cell_x] = 254
    return costmap


def _footprint():
    message = PolygonStamped()
    message.header.frame_id = 'odom'
    for x, y in ((0.5, 0.35), (0.5, -0.35),
                 (-1.2, -0.35), (-1.2, 0.35)):
        point = Point32()
        point.x = x
        point.y = y
        message.polygon.points.append(point)
    return message


def test_costmap_arc_rejects_blocked_left_and_keeps_clear_right():
    costmap = _costmap_with_obstacle(0.0, -1.0)
    polygon = [(0.5, 0.35), (0.5, -0.35),
               (-1.2, -0.35), (-1.2, 0.35)]

    left = _evaluate_turn_arc(
        costmap, polygon, (0.0, 0.0), 'left', math.pi,
        math.radians(5.0), 253,
    )
    right = _evaluate_turn_arc(
        costmap, polygon, (0.0, 0.0), 'right', -math.pi,
        math.radians(5.0), 253,
    )

    assert not left.safe
    assert left.reason == 'carpisma'
    assert right.safe
    assert right.minimum_clearance > 0.0


def test_station_direction_selector_uses_live_costmap_and_footprint():
    manager = MissionManager.__new__(MissionManager)
    manager._lock = threading.RLock()
    manager._local_costmap = _costmap_with_obstacle(0.0, -1.0)
    manager._local_costmap_seen = time.monotonic()
    manager._local_footprint = _footprint()
    manager._local_footprint_seen = time.monotonic()
    transform = TransformStamped()
    transform.header.frame_id = 'odom'
    transform.child_frame_id = 'base_footprint'
    transform.transform.rotation.w = 1.0
    manager._fresh_base_transform = lambda _frame, _label: transform
    parameters = {
        'station_turn_costmap_max_age_s': 1.5,
        'station_turn_footprint_max_age_s': 1.5,
        'station_turn_arc_step_deg': 5.0,
        'station_turn_collision_cost': 253,
    }
    manager.get_parameter = lambda name: SimpleNamespace(
        value=parameters[name]
    )
    manager.events = []
    manager._event = lambda name, **fields: manager.events.append(
        (name, fields)
    )

    selected = manager._select_station_turn_direction('A3', 0.0, math.pi)

    assert selected == 'right'
    event, fields = manager.events[-1]
    assert event == 'station_turn_direction_selected'
    assert fields['selected_direction'] == 'right'
    assert fields['left']['safe'] is False
    assert fields['right']['safe'] is True


def test_station_turn_closes_encoder_error_not_map_residual():
    manager = _station_manager([
        0.0,
        math.radians(179.0),
        math.radians(179.0),
    ], turn_direction='left', main_measured_turn=math.radians(160.0))

    manager._turn_at_station('A3')

    assert [math.degrees(item[1]) for item in manager.operations] \
        == pytest.approx([180.0, 20.0])
    assert manager.action_calls == 1
    completed = next(
        fields for event, fields in manager.events
        if event == 'station_turn_completed'
    )
    assert completed['correction_attempts'] == 1
    assert math.degrees(completed['yaw_error_rad']) == pytest.approx(0.0)
    assert math.degrees(completed['map_yaw_error_rad']) == pytest.approx(1.0)


def test_station_turn_corrects_field_case_when_map_claims_target_reached():
    approach_xy = (4.077094, -2.497844)
    dock_xy = (5.322112, -2.528911)
    dock_path_heading = math.atan2(
        dock_xy[1] - approach_xy[1],
        dock_xy[0] - approach_xy[0],
    )
    target_heading = MissionManager._wrap_angle(
        dock_path_heading + math.pi
    )
    start_heading = math.radians(5.083)
    measured_main_turn = math.radians(161.141)
    manager = _station_manager(
        [start_heading, target_heading, target_heading],
        station='A2',
        approach_xy=approach_xy,
        dock_xy=dock_xy,
        turn_direction='left',
        main_measured_turn=measured_main_turn,
    )
    manager._encoder_yaw = start_heading
    manager._filtered_yaw = start_heading

    manager._turn_at_station('A2')

    expected_turn = MissionManager._directed_turn(
        start_heading, target_heading, 'left'
    )
    assert math.degrees(manager.operations[0][1]) == pytest.approx(
        173.491, abs=0.01
    )
    assert manager.operations[1][0] == 'station_turn_correction:A2'
    assert manager.operations[1][1] == pytest.approx(
        expected_turn - measured_main_turn
    )
    completed = next(
        fields for event, fields in manager.events
        if event == 'station_turn_completed'
    )
    assert completed['correction_attempts'] == 1
    assert completed['encoder_turn_error_rad'] == pytest.approx(0.0)


def test_aborted_main_spin_uses_raw_bounded_corrections():
    manager = _station_manager([
        0.0,
        math.radians(170.0),
        math.radians(179.0),
    ], failed_action_calls=(1,), turn_direction='left',
        main_measured_turn=math.radians(170.0))

    manager._turn_at_station('A3')

    assert len(manager.operations) == 2
    completed = next(
        fields for event, fields in manager.events
        if event == 'station_turn_completed'
    )
    assert completed['main_action_outcome'] == 'action_status_6'
    corrections = [
        fields for event, fields in manager.events
        if event == 'station_turn_correction_finished'
    ]
    assert corrections[0]['outcome'] == 'success'
    assert corrections[0]['odometry_source'] == '/odom'
    assert completed['correction_attempts'] == 1


def test_station_heading_aborts_only_after_five_correction_attempts():
    manager = _station_manager([
        0.0,
        math.radians(170.0),
        math.radians(170.0),
        math.radians(170.0),
        math.radians(170.0),
        math.radians(170.0),
        math.radians(170.0),
    ], turn_direction='left', main_measured_turn=math.radians(170.0),
        correction_measured_scale=0.0)

    with pytest.raises(MissionAbort, match='correction 5/5'):
        manager._turn_at_station('A3')

    assert len(manager.operations) == 6
    assert sum(
        event == 'station_turn_correction_finished'
        for event, _fields in manager.events
    ) == 5
