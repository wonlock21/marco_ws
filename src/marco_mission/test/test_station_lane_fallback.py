"""Station lane docking to reverse Nav2 fallback regression tests."""

import json
import math
import threading
import time
from types import SimpleNamespace

import pytest
from action_msgs.msg import GoalStatus
from rclpy.time import Time
from std_msgs.msg import Bool

from marco_mission import mission_manager
from marco_mission.mission_manager import MissionAbort
from marco_mission.mission_manager import MissionActionFailure
from marco_mission.mission_manager import MissionManager
from marco_mission.mission_manager import _station_fallback_pose_geometry
from marco_mission.mission_manager import _station_fallback_remaining_path
from marco_mission.mission_manager import _remaining_polyline_from_pose
from marco_msgs.action import DockToStation
from marco_msgs.msg import RobotStatus


class _Publisher:
    def __init__(self, operations):
        self.operations = operations

    def publish(self, message):
        self.operations.append(('lane', message.data))


class _TwistPublisher:
    def __init__(self, operations):
        self.operations = operations

    def publish(self, message):
        self.operations.append(
            ('nav_zero', message.linear.x, message.angular.z)
        )


class _DoneFuture:
    def __init__(self, result):
        self._result = result

    def done(self):
        return True

    def result(self):
        return self._result


class _GoalHandle:
    accepted = True

    def __init__(self, wrapped_result):
        self.wrapped_result = wrapped_result
        self.cancelled = False

    def get_result_async(self):
        return _DoneFuture(self.wrapped_result)

    def cancel_goal_async(self):
        self.cancelled = True


class _ActionClient:
    def __init__(self, handle):
        self.handle = handle

    def wait_for_server(self, timeout_sec):
        return True

    def send_goal_async(self, goal, feedback_callback=None):
        return _DoneFuture(self.handle)


def _dock_result(code, message='dock failed'):
    result = DockToStation.Result()
    result.success = code in (
        DockToStation.Result.RESULT_OK,
        DockToStation.Result.RESULT_LOAD_DETECTED,
    )
    result.result_code = code
    result.message = message
    return result


def _dock_feedback(active=True):
    return SimpleNamespace(feedback=SimpleNamespace(
        configured_duration_s=0.0,
        elapsed_s=1.0,
        remaining_s=0.0,
        lane_control_active=active,
        camera_valid=True,
        stopped=False,
    ))


def _graph_feature(feature_id, start_id, end_id, coordinates, direction):
    return {
        'type': 'Feature',
        'properties': {
            'id': feature_id,
            'startid': start_id,
            'endid': end_id,
            'metadata': {
                'movement_direction': direction,
                'load_rule': 'any',
            },
        },
        'geometry': {
            'type': 'MultiLineString',
            'coordinates': [coordinates],
        },
    }


def _manager(
    tmp_path,
    stations=('A1',),
    result_codes=(),
    edge_direction='reverse',
):
    manager = MissionManager.__new__(MissionManager)
    manager._nodes = {}
    features = []
    station_geometry = {}
    for index, station in enumerate(stations):
        base_x = float(index * 2)
        dock_id = index * 10 + 1
        approach_id = index * 10 + 2
        approach_name = f'{station}_yaklasma'
        role_prefix = 'pickup' if station.startswith('A') else 'dropoff'
        manager._nodes[station] = {
            'id': dock_id,
            'name': station,
            'xy': [base_x, -1.0],
            'station_id': station,
            'role': f'{role_prefix}_dock',
        }
        manager._nodes[approach_name] = {
            'id': approach_id,
            'name': approach_name,
            'xy': [base_x, 0.0],
            'station_id': station,
            'role': f'{role_prefix}_approach',
        }
        features.append(_graph_feature(
            100 + index,
            approach_id,
            dock_id,
            [[base_x, 0.0], [base_x, -0.5], [base_x, -1.0]],
            edge_direction,
        ))
        station_geometry[station] = (base_x, math.pi / 2.0)
    graph_file = tmp_path / 'route.geojson'
    graph_file.write_text(json.dumps({
        'type': 'FeatureCollection',
        'features': features,
    }), encoding='utf-8')
    manager._graph_file = str(graph_file)
    manager._action_timeout = 120.0
    manager._lock = threading.RLock()
    manager._busy = True
    manager._running = True
    manager._estop = False
    manager._latched_abort = False
    manager._manual = False
    manager._obstacle = False
    manager._require_base_communication = False
    manager._base_communication_ok = True
    manager._base_communication_seen = time.monotonic()
    manager._load_detected = False
    manager._load_detected_wall = time.monotonic()
    manager._load_detected_sequence = 1
    manager._load_true_since = 0.0
    manager._load_true_samples = 0
    manager._pickup_contact_session = None
    manager._pickup_contact_session_sequence = 0
    manager._pickup_lift_started = False
    manager._pickup_completed = False
    manager._pickup_completion_source = ''
    manager._dock = object()
    manager._follow_path = object()
    manager._station_phase = manager._STATION_LINE_FOLLOW_READY
    manager._current_node = 'approach'
    manager._edge = ''
    manager.operations = []
    manager.events = []
    manager._task_pub = _Publisher(manager.operations)
    manager._precise_turn_correction_pub = _TwistPublisher(
        manager.operations
    )
    manager._safe_stop = lambda: manager.operations.append(('speed_reset',))
    manager._event = lambda name, **fields: manager.events.append(
        (name, fields)
    )
    manager._wait_until_stopped = (
        lambda label, **_kwargs: manager.operations.append(
            ('stopped', label)
        )
    )
    manager._await_route_constraints = lambda: None
    manager._set_state = lambda state, target='': manager.operations.append(
        ('state', state, target)
    )
    parameters = {
        'junction_path_match_tolerance_m': 0.25,
        'station_fallback_max_cross_track_m': 0.60,
        'station_fallback_max_heading_error_deg': 35.0,
        'station_fallback_along_track_margin_m': 0.15,
        'load_detected_freshness_s': 0.25,
        'load_detected_debounce_s': 0.075,
    }
    manager.get_parameter = lambda name: SimpleNamespace(
        value=parameters[name]
    )
    manager.get_clock = lambda: SimpleNamespace(
        now=lambda: Time(nanoseconds=1_000_000_000)
    )
    first_x, first_yaw = station_geometry[stations[0]]
    manager.pose_sequence = [
        (first_x, -0.45, first_yaw),
        (first_x, -1.0, first_yaw),
    ]

    def fresh_pose(_label):
        if len(manager.pose_sequence) > 1:
            return manager.pose_sequence.pop(0)
        return manager.pose_sequence[0]

    manager._fresh_map_base_pose = fresh_pose
    manager.dock_feedback = []
    codes = iter(result_codes)

    def action(
        client, goal, label, _timeout=None, require_turn_sensors=False,
        feedback_callback=None, interrupt_callback=None,
    ):
        if client is manager._dock:
            manager.operations.append(('dock', label))
            if feedback_callback is not None:
                for feedback in manager.dock_feedback:
                    feedback_callback(feedback)
            code = next(codes, DockToStation.Result.RESULT_OK)
            if code not in (
                DockToStation.Result.RESULT_OK,
                DockToStation.Result.RESULT_LOAD_DETECTED,
            ):
                raise MissionActionFailure(
                    label,
                    GoalStatus.STATUS_ABORTED,
                    _dock_result(code),
                )
            return _dock_result(code, 'lane end and measured stop')
        assert client is manager._follow_path
        assert require_turn_sensors is True
        manager.operations.append(('follow', label, goal))
        if interrupt_callback is not None and interrupt_callback():
            return mission_manager._ACTION_INTERRUPTED_BY_LOAD
        return SimpleNamespace()

    manager._action = action
    return manager


def _dock_then_lift(manager, station, pickup):
    lifts = []
    manager._do_lift = lambda target, pickup: lifts.append(
        (target, pickup)
    )
    manager._do_dock(station, pickup)
    manager._do_lift(station, pickup)
    return lifts


def _follow_goal(manager):
    return next(
        item[2] for item in manager.operations if item[0] == 'follow'
    )


def test_action_failure_retains_terminal_result_payload():
    manager = MissionManager.__new__(MissionManager)
    payload = _dock_result(DockToStation.Result.RESULT_LANE_LOST)
    wrapped = SimpleNamespace(
        status=GoalStatus.STATUS_ABORTED,
        result=payload,
    )
    handle = _GoalHandle(wrapped)
    manager._action_timeout = 2.0
    manager._lock = threading.Lock()
    manager._active_goal = None
    manager._active_kind = ''
    manager._abort_reason = ''
    manager._check_abort = lambda: None
    manager._check_action_health = lambda _required=False: None
    manager._route_guard_abort_for_action = lambda _label, _start: ''
    manager._event = lambda _name, **_fields: None

    with pytest.raises(MissionActionFailure) as caught:
        manager._action(
            _ActionClient(handle), object(), 'lane_end_docking:A1')

    assert caught.value.status == GoalStatus.STATUS_ABORTED
    assert caught.value.result is payload


def test_dropoff_pose_feedback_requests_one_stop_and_accepts_handoff(
    tmp_path,
):
    manager = _manager(
        tmp_path, ('B2',),
        (DockToStation.Result.RESULT_CONTROL_INACTIVE,),
    )
    manager.dock_feedback = [_dock_feedback(), _dock_feedback()]
    manager.pose_sequence = [
        (0.09, -1.0, math.pi / 2.0 + math.radians(14.0)),
        (0.07, -1.0, math.pi / 2.0 + math.radians(7.0)),
    ]

    manager._do_dock('B2', pickup=False)

    assert manager.operations.count(('lane', 'STOP')) == 1
    assert manager.operations.count(('speed_reset',)) == 1
    assert not any(item[0] == 'follow' for item in manager.operations)
    assert manager._station_phase == manager._STATION_DROPOFF_READY
    handoff = next(
        fields for name, fields in manager.events
        if name == 'dock_pose_stop_handoff'
    )
    assert handoff['dock_result_code'] == (
        DockToStation.Result.RESULT_CONTROL_INACTIVE)
    completed = next(
        fields for name, fields in manager.events
        if name == 'dock_pose_reverse_docking_completed'
    )
    assert completed['completion_source'] == 'dock_pose'
    stop_index = manager.operations.index(('lane', 'STOP'))
    reset_index = manager.operations.index(('speed_reset',))
    measured_stop_index = manager.operations.index(
        ('stopped', 'B2 dock-pose durusu'))
    assert stop_index < measured_stop_index
    assert reset_index < measured_stop_index


def test_pose_feedback_outside_trigger_does_not_request_stop(tmp_path):
    manager = _manager(tmp_path, ('B2',))
    manager.dock_feedback = [_dock_feedback()]
    manager.pose_sequence = [
        (0.101, -1.0, math.pi / 2.0),
        (0.0, -1.0, math.pi / 2.0),
    ]

    manager._do_dock('B2', pickup=False)

    assert ('lane', 'STOP') not in manager.operations
    assert ('speed_reset',) not in manager.operations
    assert not any(
        name == 'dock_pose_stop_requested'
        for name, _fields in manager.events
    )
    assert any(
        name == 'lane_end_reverse_docking_completed'
        for name, _fields in manager.events
    )


def test_pose_stop_near_but_outside_strict_runs_verified_refinement(
    tmp_path,
):
    manager = _manager(
        tmp_path, ('A1',),
        (DockToStation.Result.RESULT_CONTROL_INACTIVE,),
    )
    manager.dock_feedback = [_dock_feedback()]
    near_pose = (0.10, -1.0, math.pi / 2.0)
    manager.pose_sequence = [
        near_pose,
        near_pose,
        near_pose,
        (0.0, -1.0, math.pi / 2.0),
    ]

    manager._do_dock('A1', pickup=True)

    assert len([
        item for item in manager.operations if item[0] == 'follow'
    ]) == 1
    assert manager._pickup_completion_source == 'nav2_refinement'
    assert any(
        name == 'dock_pose_near_refinement_started'
        for name, _fields in manager.events
    )
    assert any(
        name == 'station_lane_fallback_pose_verified'
        for name, _fields in manager.events
    )


def test_pose_stop_outside_safe_refinement_region_cannot_complete(tmp_path):
    manager = _manager(
        tmp_path, ('B2',),
        (DockToStation.Result.RESULT_CONTROL_INACTIVE,),
    )
    manager.dock_feedback = [_dock_feedback()]
    manager.pose_sequence = [
        (0.10, -1.0, math.pi / 2.0),
        (0.151, -1.0, math.pi / 2.0),
    ]

    with pytest.raises(MissionAbort, match='refinement bolgesi disinda'):
        manager._do_dock('B2', pickup=False)

    assert not any(item[0] == 'follow' for item in manager.operations)
    assert not any(
        name == 'dock_pose_reverse_docking_completed'
        for name, _fields in manager.events
    )


@pytest.mark.parametrize('invalid_pose', [
    (math.nan, -1.0, math.pi / 2.0),
    (0.0, -1.0, math.inf),
])
def test_non_finite_feedback_pose_cannot_trigger_stop(tmp_path, invalid_pose):
    manager = _manager(
        tmp_path, ('B2',),
        (DockToStation.Result.RESULT_ABORTED,),
    )
    manager.dock_feedback = [_dock_feedback()]
    manager.pose_sequence = [invalid_pose]

    with pytest.raises(MissionActionFailure):
        manager._do_dock('B2', pickup=False)

    assert ('lane', 'STOP') not in manager.operations
    assert ('speed_reset',) not in manager.operations
    assert not any(
        name == 'dock_pose_stop_requested'
        for name, _fields in manager.events
    )


def test_failed_fresh_pose_lookup_cannot_trigger_stop(tmp_path):
    manager = _manager(
        tmp_path, ('B2',),
        (DockToStation.Result.RESULT_ABORTED,),
    )
    manager.dock_feedback = [_dock_feedback()]
    manager._fresh_map_base_pose = lambda _label: (_ for _ in ()).throw(
        MissionAbort('map TF bayat/kayip')
    )

    with pytest.raises(MissionActionFailure):
        manager._do_dock('B2', pickup=False)

    assert ('lane', 'STOP') not in manager.operations
    assert ('speed_reset',) not in manager.operations
    assert not any(
        name == 'dock_pose_stop_requested'
        for name, _fields in manager.events
    )


@pytest.mark.parametrize(
    'station,pickup,position_error,yaw_error_deg',
    [
        ('A1', True, 0.050, 4.0),
        ('A1', True, 0.075, 8.0),
        ('B2', False, 0.050, 4.0),
        ('B2', False, 0.075, 8.0),
    ],
)
def test_visual_lane_end_inside_final_pose_goes_directly_to_lift(
    tmp_path, station, pickup, position_error, yaw_error_deg,
):
    manager = _manager(tmp_path, (station,))
    dock_x = float(manager._nodes[station]['xy'][0])
    manager.pose_sequence = [(
        dock_x + position_error,
        -1.0,
        math.pi / 2.0 + math.radians(yaw_error_deg),
    )]

    lifts = _dock_then_lift(manager, station, pickup)

    assert not any(item[0] == 'follow' for item in manager.operations)
    assert not any(
        name == 'station_lane_fallback_started'
        for name, _fields in manager.events
    )
    assert lifts == [(station, pickup)]
    verified = next(
        fields for name, fields in manager.events
        if name == 'lane_end_pose_verified'
    )
    assert verified['position_error_m'] == pytest.approx(position_error)
    assert verified['yaw_error_deg'] == pytest.approx(yaw_error_deg)


@pytest.mark.parametrize(
    'position_error,yaw_error_deg',
    [
        (0.076, 0.0),
        (0.100, 0.0),
        (0.150, 0.0),
        (0.050, 9.0),
    ],
)
def test_visual_lane_end_near_pose_runs_one_short_refinement(
    tmp_path, position_error, yaw_error_deg,
):
    manager = _manager(tmp_path, ('A1',))
    near_pose = (
        position_error,
        -1.0,
        math.pi / 2.0 + math.radians(yaw_error_deg),
    )
    manager.pose_sequence = [
        near_pose,
        near_pose,
        (0.0, -1.0, math.pi / 2.0),
    ]

    lifts = _dock_then_lift(manager, 'A1', True)

    assert lifts == [('A1', True)]
    assert len([
        item for item in manager.operations if item[0] == 'follow'
    ]) == 1
    started = next(
        fields for name, fields in manager.events
        if name == 'lane_end_near_refinement_started'
    )
    assert started['position_error_m'] == pytest.approx(position_error)
    assert started['yaw_error_deg'] == pytest.approx(yaw_error_deg)
    assert not any(
        name == 'premature_lane_end'
        for name, _fields in manager.events
    )


@pytest.mark.parametrize('visual_pose', [
    (0.0, -0.849, math.pi / 2.0),
    (0.0, -0.450, math.pi / 2.0),
])
def test_visual_lane_end_beyond_near_threshold_uses_full_fallback(
    tmp_path, visual_pose,
):
    manager = _manager(tmp_path, ('A1',))
    manager.pose_sequence = [
        visual_pose,
        visual_pose,
        (0.0, -1.0, math.pi / 2.0),
    ]

    lifts = _dock_then_lift(manager, 'A1', True)

    assert lifts == [('A1', True)]
    premature = next(
        fields for name, fields in manager.events
        if name == 'premature_lane_end'
    )
    expected_error = math.hypot(visual_pose[0], visual_pose[1] + 1.0)
    assert premature['position_error_m'] == pytest.approx(expected_error)
    assert any(
        name == 'station_lane_fallback_started'
        for name, _fields in manager.events
    )
    assert not any(
        name == 'lane_end_near_refinement_started'
        for name, _fields in manager.events
    )


@pytest.mark.parametrize(
    'final_pose,success',
    [
        ((0.074, -1.0, math.pi / 2.0 + math.radians(7.9)), True),
        ((0.076, -1.0, math.pi / 2.0), False),
        ((0.0, -1.0, math.pi / 2.0 + math.radians(8.1)), False),
    ],
)
def test_near_refinement_requires_final_pose_authority(
    tmp_path, final_pose, success,
):
    manager = _manager(tmp_path, ('A1',))
    near_pose = (0.100, -1.0, math.pi / 2.0)
    manager.pose_sequence = [near_pose, near_pose, final_pose]
    lifts = []
    manager._do_lift = lambda station, pickup: lifts.append(
        (station, pickup)
    )

    if success:
        manager._do_dock('A1', True)
        manager._do_lift('A1', True)
    else:
        with pytest.raises(MissionAbort, match='dock pose dogrulanamadi'):
            manager._do_dock('A1', True)
            manager._do_lift('A1', True)

    assert lifts == ([('A1', True)] if success else [])


@pytest.mark.parametrize(
    'result_code',
    [
        DockToStation.Result.RESULT_LANE_LOST,
        DockToStation.Result.RESULT_CONTROL_INACTIVE,
        DockToStation.Result.RESULT_CAMERA_LOST,
    ],
)
def test_pickup_recoverable_failure_uses_safe_reverse_dock_fallback(
    tmp_path, result_code,
):
    manager = _manager(tmp_path, ('A1',), (result_code,))

    lifts = _dock_then_lift(manager, 'A1', True)

    lane_index = manager.operations.index(('lane', 'STOP'))
    stopped_index = next(
        index for index, item in enumerate(manager.operations)
        if item[0] == 'stopped'
    )
    follow_index = next(
        index for index, item in enumerate(manager.operations)
        if item[0] == 'follow'
    )
    assert lane_index < stopped_index < follow_index
    assert lifts == [('A1', True)]
    assert manager._station_phase == manager._STATION_PICKUP_READY
    assert manager._current_node == 'A1'
    assert _follow_goal(manager).path.poses[-1].pose.position.y == -1.0
    started = next(
        fields for name, fields in manager.events
        if name == 'station_lane_fallback_started'
    )
    assert started['dock_result_code'] == result_code
    assert any(
        name == 'station_lane_fallback_pose_verified'
        for name, _fields in manager.events
    )
    if result_code == DockToStation.Result.RESULT_CONTROL_INACTIVE:
        assert not any(
            name == 'dock_pose_stop_handoff'
            for name, _fields in manager.events
        )


def test_dropoff_lane_lost_fallback_navigates_loaded_then_lifts(tmp_path):
    manager = _manager(
        tmp_path, ('B2',), (DockToStation.Result.RESULT_LANE_LOST,)
    )

    lifts = _dock_then_lift(manager, 'B2', False)

    assert ('state', RobotStatus.STATE_MOVING_LOADED, 'B2') in manager.operations
    assert lifts == [('B2', False)]
    assert manager._station_phase == manager._STATION_DROPOFF_READY


def test_fallback_path_starts_at_current_pose_and_never_returns_to_approach(
    tmp_path,
):
    manager = _manager(
        tmp_path, ('A1',), (DockToStation.Result.RESULT_LANE_LOST,)
    )
    manager.pose_sequence = [
        (0.04, -0.45, math.pi / 2.0),
        (0.0, -1.0, math.pi / 2.0),
    ]

    manager._do_dock('A1', True)

    path = _follow_goal(manager).path
    coordinates = [
        (pose.pose.position.x, pose.pose.position.y)
        for pose in path.poses
    ]
    assert coordinates[0] == pytest.approx((0.04, -0.45))
    assert coordinates[-1] == pytest.approx((0.0, -1.0))
    assert all(y <= -0.45 for _x, y in coordinates)
    assert (0.0, 0.0) not in coordinates
    assert all(
        math.isclose(
            2.0 * math.atan2(
                pose.pose.orientation.z, pose.pose.orientation.w
            ),
            math.pi / 2.0,
            abs_tol=1.0e-6,
        )
        for pose in path.poses
    )


def test_remaining_polyline_drops_all_geometry_behind_current_pose():
    remaining, cross_track = _remaining_polyline_from_pose(
        [(0.0, 0.0), (0.0, -0.5), (0.0, -1.0)],
        0.0,
        -0.65,
        0.25,
    )

    assert cross_track == pytest.approx(0.0)
    assert remaining == pytest.approx([(0.0, -0.65), (0.0, -1.0)])


@pytest.mark.parametrize(
    ('cross_track', 'accepted'),
    [
        (0.20, True),
        (0.30, True),
        (0.40, True),
        (0.60, True),
        (0.61, False),
    ],
)
def test_station_fallback_cross_track_contract(cross_track, accepted):
    arguments = (
        [(0.0, 0.0), (0.0, -1.0)],
        cross_track,
        -0.50,
        math.pi / 2.0,
        0.60,
        math.radians(35.0),
        0.15,
    )

    if accepted:
        projection, heading_error = _station_fallback_pose_geometry(
            *arguments)
        assert projection.cross_track == pytest.approx(cross_track)
        assert heading_error == pytest.approx(0.0)
    else:
        with pytest.raises(MissionAbort, match='cross-track fazla'):
            _station_fallback_pose_geometry(*arguments)


@pytest.mark.parametrize(
    ('heading_error_deg', 'accepted'),
    [
        (30.0, True),
        (35.0, True),
        (36.0, False),
        (50.0, False),
    ],
)
def test_station_fallback_reverse_heading_contract(
    heading_error_deg, accepted,
):
    arguments = (
        [(0.0, 0.0), (0.0, -1.0)],
        0.30,
        -0.50,
        math.pi / 2.0 + math.radians(heading_error_deg),
        0.60,
        math.radians(35.0),
        0.15,
    )

    if accepted:
        _projection, heading_error = _station_fallback_pose_geometry(
            *arguments)
        assert math.degrees(heading_error) == pytest.approx(
            heading_error_deg)
    else:
        with pytest.raises(MissionAbort, match='heading uyumsuz'):
            _station_fallback_pose_geometry(*arguments)


@pytest.mark.parametrize(
    ('robot_y', 'expected_along', 'accepted'),
    [
        (-0.50, 0.50, True),
        (0.10, -0.10, True),
        (0.16, -0.16, False),
        (-1.10, 1.10, True),
        (-1.16, 1.16, False),
    ],
)
def test_station_fallback_along_track_corridor(
    robot_y, expected_along, accepted,
):
    arguments = (
        [(0.0, 0.0), (0.0, -1.0)],
        0.20,
        robot_y,
        math.pi / 2.0,
        0.60,
        math.radians(35.0),
        0.15,
    )

    if accepted:
        projection, _heading_error = _station_fallback_pose_geometry(
            *arguments)
        assert projection.along_track == pytest.approx(expected_along)
    else:
        with pytest.raises(MissionAbort, match='along-track corridor'):
            _station_fallback_pose_geometry(*arguments)


def test_controlled_merge_starts_at_robot_and_uses_only_forward_suffix():
    points = [(0.0, 0.0), (0.0, -0.5), (0.0, -1.0)]
    projection, _heading_error = _station_fallback_pose_geometry(
        points,
        0.30,
        -0.20,
        math.pi / 2.0,
        0.60,
        math.radians(35.0),
        0.15,
    )

    remaining, merge_point, merge_used = _station_fallback_remaining_path(
        points, 0.30, -0.20, projection)

    assert merge_used is True
    assert remaining[0] == pytest.approx((0.30, -0.20))
    assert merge_point == pytest.approx((0.0, -0.65))
    assert remaining[1] == pytest.approx(merge_point)
    assert remaining[-1] == pytest.approx((0.0, -1.0))
    assert (0.0, 0.0) not in remaining
    assert all(
        current[1] >= following[1]
        for current, following in zip(remaining, remaining[1:])
    )


def test_station_fallback_uses_station_limits_and_reports_geometry(tmp_path):
    manager = _manager(
        tmp_path, ('A1',), (DockToStation.Result.RESULT_LANE_LOST,)
    )
    original_get_parameter = manager.get_parameter
    manager.get_parameter = lambda name: (
        SimpleNamespace(value=0.01)
        if name == 'junction_path_match_tolerance_m'
        else original_get_parameter(name)
    )
    manager.pose_sequence = [
        (0.40, -0.45, math.pi / 2.0),
        (0.0, -1.0, math.pi / 2.0),
    ]

    manager._do_dock('A1', True)

    event = next(
        fields for name, fields in manager.events
        if name == 'station_lane_fallback_path_planned'
    )
    assert event['cross_track_error_m'] == pytest.approx(0.40)
    assert event['projected_along_track_m'] == pytest.approx(0.45)
    assert event['total_edge_length_m'] == pytest.approx(1.0)
    assert event['heading_error_deg'] == pytest.approx(0.0)
    assert event['merge_used'] is True


@pytest.mark.parametrize(
    'final_pose,reason',
    [
        ((0.0, 0.0, math.pi / 2.0), 'dock pose dogrulanamadi'),
        ((0.0, -0.90, math.pi / 2.0), 'konum hatasi=0.100'),
        ((0.0, -1.0, math.pi / 2.0 + math.radians(8.1)),
         'yon hatasi=8.1'),
    ],
)
def test_follow_success_outside_final_dock_pose_prevents_lift(
    tmp_path, final_pose, reason,
):
    manager = _manager(
        tmp_path, ('A1',), (DockToStation.Result.RESULT_LANE_LOST,)
    )
    manager.pose_sequence = [
        (0.0, -0.45, math.pi / 2.0),
        final_pose,
    ]
    lifts = []
    manager._do_lift = lambda station, pickup: lifts.append((station, pickup))

    with pytest.raises(MissionAbort, match=reason):
        manager._do_dock('A1', True)
        manager._do_lift('A1', True)

    assert lifts == []
    assert manager._current_node == 'approach'
    assert not any(
        name == 'station_lane_fallback_completed'
        for name, _fields in manager.events
    )


def test_final_yaw_inside_eight_degree_limit_allows_lift(tmp_path):
    manager = _manager(
        tmp_path, ('A1',), (DockToStation.Result.RESULT_LANE_LOST,)
    )
    manager.pose_sequence = [
        (0.0, -0.45, math.pi / 2.0),
        (0.0, -1.0, math.pi / 2.0 + math.radians(7.9)),
    ]

    lifts = _dock_then_lift(manager, 'A1', True)

    assert lifts == [('A1', True)]
    assert manager._current_node == 'A1'


def test_invalid_localization_prevents_fallback_and_lift(tmp_path):
    manager = _manager(
        tmp_path, ('A1',), (DockToStation.Result.RESULT_LANE_LOST,)
    )
    manager._fresh_map_base_pose = lambda _label: (_ for _ in ()).throw(
        MissionAbort('lokalizasyon/TF gecersiz')
    )
    lifts = []
    manager._do_lift = lambda station, pickup: lifts.append((station, pickup))

    with pytest.raises(MissionAbort, match='lokalizasyon/TF gecersiz'):
        manager._do_dock('A1', True)
        manager._do_lift('A1', True)

    assert lifts == []


def test_non_reverse_station_edge_fails_closed(tmp_path):
    manager = _manager(
        tmp_path,
        ('A1',),
        (DockToStation.Result.RESULT_LANE_LOST,),
        edge_direction='forward',
    )

    with pytest.raises(MissionAbort, match='approach->dock kenari reverse degil'):
        manager._do_dock('A1', True)

    assert not any(item[0] == 'follow' for item in manager.operations)
    assert manager._current_node == 'approach'


def test_current_node_changes_only_after_follow_and_pose_verification(tmp_path):
    manager = _manager(
        tmp_path, ('A1',), (DockToStation.Result.RESULT_LANE_LOST,)
    )
    original_action = manager._action

    def action(*args, **kwargs):
        result = original_action(*args, **kwargs)
        if args[0] is manager._follow_path:
            assert manager._current_node == 'approach'
        return result

    manager._action = action

    manager._do_dock('A1', True)

    assert manager._current_node == 'A1'


def test_fallback_is_per_station_and_next_station_retries_lane(tmp_path):
    manager = _manager(
        tmp_path,
        ('A1', 'B2'),
        (
            DockToStation.Result.RESULT_LANE_LOST,
            DockToStation.Result.RESULT_OK,
        ),
    )

    manager._do_dock('A1', True)
    manager.pose_sequence = [(2.0, -1.0, math.pi / 2.0)]
    manager._do_dock('B2', False)

    dock_calls = [item for item in manager.operations if item[0] == 'dock']
    follow_calls = [item for item in manager.operations if item[0] == 'follow']
    assert len(dock_calls) == 2
    assert len(follow_calls) == 1
    assert follow_calls[0][1].endswith(':A1')


def test_reverse_lane_fallback_is_followed_by_forward_station_exit(tmp_path):
    manager = _manager(
        tmp_path, ('A1',), (DockToStation.Result.RESULT_LANE_LOST,)
    )
    exits = []
    manager._navigate = lambda target, loaded, **kwargs: exits.append(
        (target, loaded, kwargs)
    )

    manager._do_dock('A1', True)
    manager._exit_station('A1', loaded=True)

    follow = next(
        item for item in manager.operations if item[0] == 'follow'
    )
    assert follow[1].endswith(':A1')
    assert exits == [(
        'A1_yaklasma',
        True,
        {
            'explicit_start': 'A1',
            'required_direct_direction': 'forward',
        },
    )]


@pytest.mark.parametrize(
    'result_code',
    [
        DockToStation.Result.RESULT_OBSTACLE,
        DockToStation.Result.RESULT_ABORTED,
        DockToStation.Result.RESULT_STOP_FAILED,
        DockToStation.Result.RESULT_TIMEOUT,
    ],
)
def test_non_recoverable_dock_failure_remains_fatal(
    tmp_path, result_code,
):
    manager = _manager(tmp_path, ('A1',), (result_code,))

    with pytest.raises(MissionActionFailure):
        manager._do_dock('A1', True)

    assert not any(item[0] == 'follow' for item in manager.operations)
    assert ('lane', 'STOP') not in manager.operations


def test_operator_cancel_or_estop_abort_never_falls_back(tmp_path):
    manager = _manager(tmp_path, ('A1',))

    def cancelled(*_args, **_kwargs):
        raise MissionAbort('operator cancel / estop')

    manager._action = cancelled
    with pytest.raises(MissionAbort):
        manager._do_dock('A1', True)

    assert not any(item[0] == 'follow' for item in manager.operations)


def test_fallback_nav2_failure_propagates_and_prevents_lift(tmp_path):
    manager = _manager(
        tmp_path, ('A1',), (DockToStation.Result.RESULT_LANE_LOST,)
    )
    lifts = []
    manager._do_lift = lambda station, pickup: lifts.append(
        (station, pickup)
    )
    original_action = manager._action

    def action(client, *args, **kwargs):
        if client is manager._follow_path:
            raise MissionAbort('fallback nav failed')
        return original_action(client, *args, **kwargs)

    manager._action = action

    with pytest.raises(MissionAbort, match='fallback nav failed'):
        manager._do_dock('A1', True)
        manager._do_lift('A1', True)

    assert lifts == []
    assert manager._current_node == 'approach'
    assert not any(
        name == 'station_lane_fallback_completed'
        for name, _fields in manager.events
    )


def test_lane_load_completion_source_is_distinct_and_lift_is_once(tmp_path):
    manager = _manager(
        tmp_path, ('A1',),
        (DockToStation.Result.RESULT_LOAD_DETECTED,),
    )
    manager._fresh_map_base_pose = lambda _label: (_ for _ in ()).throw(
        AssertionError('physical contact must bypass visual pose validation')
    )

    lifts = _dock_then_lift(manager, 'A1', True)

    assert lifts == [('A1', True)]
    assert manager._pickup_completion_source == 'load_detected'
    assert any(
        name == 'load_detected_reverse_docking_completed'
        for name, _fields in manager.events
    )
    assert not any(
        name == 'lane_end_reverse_docking_completed'
        for name, _fields in manager.events
    )


def test_nav2_fallback_load_interrupt_stops_then_completes_once(tmp_path):
    manager = _manager(
        tmp_path, ('A1',), (DockToStation.Result.RESULT_LANE_LOST,)
    )
    original_get_parameter = manager.get_parameter
    manager.get_parameter = lambda name: (
        SimpleNamespace(value=0.0)
        if name == 'load_detected_debounce_s'
        else original_get_parameter(name)
    )
    original_action = manager._action

    def action(client, *args, **kwargs):
        if client is manager._follow_path:
            manager._on_load_detected(Bool(data=True))
            manager._on_load_detected(Bool(data=True))
        return original_action(client, *args, **kwargs)

    manager._action = action
    lifts = _dock_then_lift(manager, 'A1', True)

    follow_index = next(
        index for index, item in enumerate(manager.operations)
        if item[0] == 'follow'
    )
    zero_index = next(
        index for index, item in enumerate(manager.operations)
        if item[0] == 'nav_zero'
    )
    contact_stop_index = next(
        index for index, item in enumerate(manager.operations)
        if item == ('stopped', 'A1 load_detected fallback durusu')
    )
    assert follow_index < zero_index < contact_stop_index
    assert lifts == [('A1', True)]
    assert manager._pickup_completion_source == 'load_detected'
    completions = [
        fields for name, fields in manager.events
        if name == 'station_lane_fallback_completed'
    ]
    assert len(completions) == 1
    assert completions[0]['completion_source'] == 'load_detected'
    assert not any(
        name == 'station_lane_fallback_pose_verified'
        for name, _fields in manager.events
    )


def test_nav2_completion_wins_race_without_duplicate_lift(tmp_path):
    manager = _manager(
        tmp_path, ('A1',), (DockToStation.Result.RESULT_LANE_LOST,)
    )
    original_action = manager._action

    def action(client, *args, **kwargs):
        if client is manager._follow_path:
            # A terminal Nav2 result is returned even if contact becomes true
            # at the boundary; the sequential station flow accepts one source.
            manager._on_load_detected(Bool(data=True))
            manager._on_load_detected(Bool(data=True))
            kwargs.pop('interrupt_callback', None)
        return original_action(client, *args, **kwargs)

    manager._action = action
    lifts = _dock_then_lift(manager, 'A1', True)

    assert lifts == [('A1', True)]
    assert manager._pickup_completion_source == 'nav2_pose'
    assert sum(
        name == 'station_lane_fallback_completed'
        for name, _fields in manager.events
    ) == 1


def test_pickup_lift_claim_is_exactly_once_after_contact(tmp_path):
    manager = _manager(tmp_path, ('A1',))
    manager._lift = object()
    manager._station_phase = manager._STATION_PICKUP_READY
    session_id = manager._begin_pickup_contact_session('A1')
    manager._pickup_completion_source = 'load_detected'
    calls = []
    manager._action = lambda *args, **kwargs: calls.append(args[2])

    manager._do_lift('A1', pickup=True)
    with pytest.raises(MissionAbort, match='zaten baslatildi'):
        manager._do_lift('A1', pickup=True)

    assert calls == ['lift:pickup']
    assert manager._pickup_completed is True
    assert manager._pickup_contact_session['id'] == session_id
    assert manager._pickup_contact_session['active'] is False


def test_pickup_lift_failure_does_not_mark_loaded_or_success(tmp_path):
    manager = _manager(tmp_path, ('A1',))
    manager._lift = object()
    manager._loaded = False
    manager._station_phase = manager._STATION_PICKUP_READY
    manager._begin_pickup_contact_session('A1')
    manager._pickup_completion_source = 'load_detected'
    manager._action = lambda *args, **kwargs: (_ for _ in ()).throw(
        MissionAbort('lift hardware fault')
    )

    with pytest.raises(MissionAbort, match='lift hardware fault'):
        manager._do_lift('A1', pickup=True)

    assert manager._loaded is False
    assert manager._pickup_completed is False
    assert manager._pickup_contact_session['active'] is False


class _CancelableResultFuture:
    def __init__(self, handle, terminal_status):
        self.handle = handle
        self.terminal_status = terminal_status

    def done(self):
        return self.handle.cancelled or self.terminal_status == 'already_done'

    def result(self):
        status = (
            GoalStatus.STATUS_SUCCEEDED
            if self.terminal_status == 'already_done'
            else GoalStatus.STATUS_CANCELED
        )
        return SimpleNamespace(status=status, result=SimpleNamespace())


class _CancelableGoalHandle:
    accepted = True

    def __init__(self, terminal_status='cancel_on_request'):
        self.cancelled = False
        self.cancel_calls = 0
        self.future = _CancelableResultFuture(self, terminal_status)

    def get_result_async(self):
        return self.future

    def cancel_goal_async(self):
        self.cancel_calls += 1
        self.cancelled = True
        return _DoneFuture(SimpleNamespace())


def _action_manager(handle):
    manager = MissionManager.__new__(MissionManager)
    manager._action_timeout = 2.0
    manager._lock = threading.RLock()
    manager._active_goal = None
    manager._active_kind = ''
    manager._abort_reason = ''
    manager._check_abort = lambda: None
    manager._check_action_health = lambda _required=False: None
    manager._route_guard_abort_for_action = lambda _label, _start: ''
    manager._ensure_pickup_contact_safety = lambda: None
    manager._precise_turn_correction_pub = _TwistPublisher([])
    manager.events = []
    manager._event = lambda name, **fields: manager.events.append(
        (name, fields)
    )
    return manager, _ActionClient(handle)


def test_follow_path_load_interrupt_cancels_action_once():
    handle = _CancelableGoalHandle()
    manager, client = _action_manager(handle)

    result = manager._action(
        client, object(), 'follow_route:station_dock_fallback:A1',
        interrupt_callback=lambda: True,
    )

    assert result is mission_manager._ACTION_INTERRUPTED_BY_LOAD
    assert handle.cancel_calls == 1


def test_terminal_nav2_result_wins_over_simultaneous_load_interrupt():
    handle = _CancelableGoalHandle(terminal_status='already_done')
    manager, client = _action_manager(handle)

    result = manager._action(
        client, object(), 'follow_route:station_dock_fallback:A1',
        interrupt_callback=lambda: True,
    )

    assert result is not mission_manager._ACTION_INTERRUPTED_BY_LOAD
    assert handle.cancel_calls == 0
