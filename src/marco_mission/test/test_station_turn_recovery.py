"""Geometry-derived station turn and bounded recovery tests."""

import math
import threading
import time
from types import SimpleNamespace

import pytest
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import Point32, PolygonStamped, TransformStamped
from nav2_msgs.msg import Costmap

from marco_mission.mission_manager import MissionAbort
from marco_mission.mission_manager import MissionActionFailure
from marco_mission.mission_manager import MissionManager
from marco_mission.mission_manager import _evaluate_turn_arc
from marco_mission.station_qr_gate import StationQrGate


def _verified_gate():
    gate = StationQrGate()
    gate.arm('A3', 'q4')
    assert gate.observe('q4', True).accepted
    return gate


def _station_manager(yaw_samples, failed_action_calls=()):
    manager = MissionManager.__new__(MissionManager)
    manager._nodes = {
        'A3': {
            # A legacy persisted value must have no effect on runtime target.
            'dock_heading_yaw': 0.25,
            'turn_direction': 'left',
        },
    }
    manager._qr_gate = _verified_gate()
    manager._spin = object()
    manager._obstacle = False
    manager._imu_enabled = False
    manager._filtered_yaw = 0.0
    manager._status_detail = ''
    manager._check_action_health = lambda require_turn_sensors=False: None
    manager._select_station_turn_direction = (
        lambda _station, _current, _target: 'right'
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

    def action(
        _client, goal, label, _timeout, require_turn_sensors=False
    ):
        call = len(manager.operations) + 1
        manager.operations.append((label, goal.target_yaw, require_turn_sensors))
        if call in failed:
            raise MissionActionFailure(label, GoalStatus.STATUS_ABORTED)

    manager._action = action
    manager._wait_until_stopped = lambda label: manager.events.append(
        ('stopped', {'label': label})
    )
    manager._event = lambda name, **fields: manager.events.append(
        (name, fields)
    )
    return manager


def test_station_target_is_route_heading_plus_pi_and_uses_auto_direction():
    approach_heading = math.radians(30.0)
    target_heading = math.radians(-150.0)
    manager = _station_manager([
        approach_heading,
        math.radians(-149.0),
    ])

    manager._turn_at_station('A3', approach_heading)

    assert len(manager.operations) == 1
    assert manager.operations[0][0] == 'station_turn:A3'
    assert manager.operations[0][1] == pytest.approx(-math.pi)
    completed = next(
        fields for event, fields in manager.events
        if event == 'station_turn_completed'
    )
    assert completed['target_yaw'] == pytest.approx(target_heading)
    assert completed['correction_attempts'] == 0
    assert manager._qr_gate.phase == StationQrGate.LINE_FOLLOW_READY


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


def test_station_turn_remeasures_fresh_tf_after_each_correction():
    manager = _station_manager([
        0.0,
        math.radians(170.0),
        math.radians(176.0),
        math.radians(179.0),
    ])

    manager._turn_at_station('A3', 0.0)

    assert [math.degrees(item[1]) for item in manager.operations] \
        == pytest.approx([-180.0, 10.0, 4.0])
    completed = next(
        fields for event, fields in manager.events
        if event == 'station_turn_completed'
    )
    assert completed['correction_attempts'] == 2
    assert math.degrees(completed['yaw_error_rad']) == pytest.approx(1.0)


def test_aborted_main_and_correction_spins_use_bounded_remeasurement():
    manager = _station_manager([
        0.0,
        math.radians(170.0),
        math.radians(175.0),
        math.radians(179.0),
    ], failed_action_calls=(1, 2))

    manager._turn_at_station('A3', 0.0)

    assert len(manager.operations) == 3
    completed = next(
        fields for event, fields in manager.events
        if event == 'station_turn_completed'
    )
    assert completed['main_action_outcome'] == 'action_status_6'
    corrections = [
        fields for event, fields in manager.events
        if event == 'station_turn_correction_finished'
    ]
    assert corrections[0]['outcome'] == 'action_status_6'
    assert completed['correction_attempts'] == 2


def test_station_heading_aborts_only_after_five_correction_attempts():
    manager = _station_manager([
        0.0,
        math.radians(170.0),
        math.radians(170.0),
        math.radians(170.0),
        math.radians(170.0),
        math.radians(170.0),
        math.radians(170.0),
    ])

    with pytest.raises(MissionAbort, match='correction 5/5'):
        manager._turn_at_station('A3', 0.0)

    assert len(manager.operations) == 6
    assert sum(
        event == 'station_turn_correction_finished'
        for event, _fields in manager.events
    ) == 5
