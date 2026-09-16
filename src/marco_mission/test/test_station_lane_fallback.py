"""Station lane docking to reverse Nav2 fallback regression tests."""

import json
import math
import threading
from types import SimpleNamespace

import pytest
from action_msgs.msg import GoalStatus
from rclpy.time import Time

from marco_mission.mission_manager import MissionAbort
from marco_mission.mission_manager import MissionActionFailure
from marco_mission.mission_manager import MissionManager
from marco_mission.mission_manager import _remaining_polyline_from_pose
from marco_msgs.action import DockToStation
from marco_msgs.msg import RobotStatus


class _Publisher:
    def __init__(self, operations):
        self.operations = operations

    def publish(self, message):
        self.operations.append(('lane', message.data))


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
    result.success = code == DockToStation.Result.RESULT_OK
    result.result_code = code
    result.message = message
    return result


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
    manager._dock = object()
    manager._follow_path = object()
    manager._station_phase = manager._STATION_LINE_FOLLOW_READY
    manager._current_node = 'approach'
    manager._edge = ''
    manager.operations = []
    manager.events = []
    manager._task_pub = _Publisher(manager.operations)
    manager._event = lambda name, **fields: manager.events.append(
        (name, fields)
    )
    manager._wait_until_stopped = lambda label: manager.operations.append(
        ('stopped', label)
    )
    manager._await_route_constraints = lambda: None
    manager._set_state = lambda state, target='': manager.operations.append(
        ('state', state, target)
    )
    manager.get_parameter = lambda name: SimpleNamespace(
        value={'junction_path_match_tolerance_m': 0.25}[name]
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
    codes = iter(result_codes)

    def action(
        client, goal, label, _timeout=None, require_turn_sensors=False,
        feedback_callback=None,
    ):
        if client is manager._dock:
            manager.operations.append(('dock', label))
            code = next(codes, DockToStation.Result.RESULT_OK)
            if code != DockToStation.Result.RESULT_OK:
                raise MissionActionFailure(
                    label,
                    GoalStatus.STATUS_ABORTED,
                    _dock_result(code),
                )
            return _dock_result(code, 'lane end and measured stop')
        assert client is manager._follow_path
        assert require_turn_sensors is True
        manager.operations.append(('follow', label, goal))
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


@pytest.mark.parametrize(
    'station,pickup',
    [('A1', True), ('B2', False)],
)
def test_lane_success_goes_directly_to_lift_without_fallback(
    tmp_path, station, pickup,
):
    manager = _manager(tmp_path, (station,))

    lifts = _dock_then_lift(manager, station, pickup)

    assert not any(item[0] == 'follow' for item in manager.operations)
    assert not any(
        name == 'station_lane_fallback_started'
        for name, _fields in manager.events
    )
    assert lifts == [(station, pickup)]


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
    manager._do_dock('B2', False)

    dock_calls = [item for item in manager.operations if item[0] == 'dock']
    follow_calls = [item for item in manager.operations if item[0] == 'follow']
    assert len(dock_calls) == 2
    assert len(follow_calls) == 1
    assert follow_calls[0][1].endswith(':A1')


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
