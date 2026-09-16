"""Station lane docking to Nav2 fallback regression tests."""

import threading
from types import SimpleNamespace

import pytest
from action_msgs.msg import GoalStatus

from marco_mission.mission_manager import MissionAbort
from marco_mission.mission_manager import MissionActionFailure
from marco_mission.mission_manager import MissionManager
from marco_msgs.action import DockToStation


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


def _manager(stations=('A1',), result_codes=()):
    manager = MissionManager.__new__(MissionManager)
    manager._nodes = {
        station: {
            'role': 'pickup_dock' if station.startswith('A')
            else 'dropoff_dock',
        }
        for station in stations
    }
    manager._action_timeout = 120.0
    manager._dock = object()
    manager._station_phase = manager._STATION_LINE_FOLLOW_READY
    manager._current_node = 'approach'
    manager.operations = []
    manager.events = []
    manager._task_pub = _Publisher(manager.operations)
    manager._event = lambda name, **fields: manager.events.append(
        (name, fields)
    )
    manager._wait_until_stopped = lambda label: manager.operations.append(
        ('stopped', label)
    )
    manager._navigate = lambda target, loaded: manager.operations.append(
        ('nav', target, loaded)
    )
    codes = iter(result_codes)

    def action(
        _client, _goal, label, _timeout, require_turn_sensors=False,
        feedback_callback=None,
    ):
        manager.operations.append(('dock', label))
        code = next(codes, DockToStation.Result.RESULT_OK)
        if code != DockToStation.Result.RESULT_OK:
            raise MissionActionFailure(
                label,
                GoalStatus.STATUS_ABORTED,
                _dock_result(code),
            )
        return _dock_result(code, 'lane end and measured stop')

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
    station, pickup,
):
    manager = _manager((station,))

    lifts = _dock_then_lift(manager, station, pickup)

    assert not any(item[0] == 'nav' for item in manager.operations)
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
def test_pickup_recoverable_lane_failure_uses_safe_nav2_fallback(
    result_code,
):
    manager = _manager(('A1',), (result_code,))

    lifts = _dock_then_lift(manager, 'A1', True)

    lane_index = manager.operations.index(('lane', 'STOP'))
    stopped_index = next(
        index for index, item in enumerate(manager.operations)
        if item[0] == 'stopped'
    )
    nav_index = manager.operations.index(('nav', 'A1', False))
    assert lane_index < stopped_index < nav_index
    assert lifts == [('A1', True)]
    assert manager._station_phase == manager._STATION_PICKUP_READY
    assert manager._current_node == 'A1'
    started = next(
        fields for name, fields in manager.events
        if name == 'station_lane_fallback_started'
    )
    assert started['dock_result_code'] == result_code


def test_dropoff_lane_lost_fallback_navigates_loaded_then_lifts():
    manager = _manager(
        ('B2',), (DockToStation.Result.RESULT_LANE_LOST,)
    )

    lifts = _dock_then_lift(manager, 'B2', False)

    assert ('nav', 'B2', True) in manager.operations
    assert lifts == [('B2', False)]
    assert manager._station_phase == manager._STATION_DROPOFF_READY


def test_fallback_is_per_station_and_next_station_retries_lane():
    manager = _manager(
        ('A1', 'B2'),
        (
            DockToStation.Result.RESULT_LANE_LOST,
            DockToStation.Result.RESULT_OK,
        ),
    )

    manager._do_dock('A1', True)
    manager._do_dock('B2', False)

    dock_calls = [item for item in manager.operations if item[0] == 'dock']
    assert len(dock_calls) == 2
    assert ('nav', 'A1', False) in manager.operations
    assert ('nav', 'B2', True) not in manager.operations


@pytest.mark.parametrize(
    'result_code',
    [
        DockToStation.Result.RESULT_OBSTACLE,
        DockToStation.Result.RESULT_ABORTED,
        DockToStation.Result.RESULT_STOP_FAILED,
        DockToStation.Result.RESULT_TIMEOUT,
    ],
)
def test_non_recoverable_dock_failure_remains_fatal(result_code):
    manager = _manager(('A1',), (result_code,))

    with pytest.raises(MissionActionFailure):
        manager._do_dock('A1', True)

    assert not any(item[0] == 'nav' for item in manager.operations)
    assert ('lane', 'STOP') not in manager.operations


def test_operator_cancel_or_estop_abort_never_falls_back():
    manager = _manager(('A1',))

    def cancelled(*_args, **_kwargs):
        raise MissionAbort('operator cancel / estop')

    manager._action = cancelled
    with pytest.raises(MissionAbort):
        manager._do_dock('A1', True)

    assert not any(item[0] == 'nav' for item in manager.operations)


def test_fallback_nav2_failure_propagates_and_prevents_lift():
    manager = _manager(
        ('A1',), (DockToStation.Result.RESULT_LANE_LOST,)
    )
    lifts = []
    manager._do_lift = lambda station, pickup: lifts.append(
        (station, pickup)
    )

    def nav_failure(_target, loaded):
        raise MissionAbort(f'fallback nav failed loaded={loaded}')

    manager._navigate = nav_failure

    with pytest.raises(MissionAbort, match='fallback nav failed'):
        manager._do_dock('A1', True)
        manager._do_lift('A1', True)

    assert lifts == []
    assert not any(
        name == 'station_lane_fallback_completed'
        for name, _fields in manager.events
    )
