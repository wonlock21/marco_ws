"""Production PLC assignment auto-start admission and race tests."""

from types import SimpleNamespace
import threading
import time

import pytest

from marco_mission.localization_validity import LocalizationHealth
from marco_mission.mission_manager import MissionManager
from marco_msgs.msg import RobotStatus


class DeferredFuture:
    """Small controllable future matching the rclpy methods used by the node."""

    def __init__(self):
        self._callbacks = []
        self._result = None
        self._exception = None
        self.cancelled = False

    def add_done_callback(self, callback):
        self._callbacks.append(callback)

    def result(self):
        if self._exception is not None:
            raise self._exception
        return self._result

    def set_result(self, result):
        self._result = result
        for callback in list(self._callbacks):
            callback(self)

    def cancel(self):
        self.cancelled = True
        return True


class FakeAssignClient:
    def __init__(self, ready=True):
        self.ready = ready
        self.calls = []

    def service_is_ready(self):
        return self.ready

    def call_async(self, request):
        future = DeferredFuture()
        self.calls.append((request, future))
        return future


class FakeReadyClient:
    def __init__(self, ready=True):
        self.ready = ready

    def service_is_ready(self):
        return self.ready


def _reply(success, task_id='plc-task-1', pickup='A1', dropoff='B3'):
    return SimpleNamespace(
        success=success,
        task_id=task_id,
        pickup_node=pickup,
        dropoff_node=dropoff,
        message='fresh assignment' if success else 'PLC CONTROL=Bekle',
    )


@pytest.fixture
def manager():
    value = MissionManager.__new__(MissionManager)
    value._lock = threading.RLock()
    value._plc_auto_start = True
    value._default_source = 'plc'
    value._state = RobotStatus.STATE_IDLE
    value._busy = False
    value._running = False
    value._plc_assign_inflight = False
    value._plc_assign_future = None
    value._plc_assign_started = 0.0
    value._plc_connected = True
    value._plc_seen = time.monotonic()
    value._plc_freshness = 3.0
    value._active_field_ready = True
    value._require_active_field = True
    value._production_route_ready = lambda: True
    value._estop = False
    value._latched_abort = False
    value._obstacle = False
    value._require_safety_supervisor = True
    value._safety_reset = FakeReadyClient()
    value._base_communication_healthy = lambda: True
    value._localization_health = lambda: LocalizationHealth(True, 'hazir')
    value._known_task_ids = set()
    value._validate_route = lambda _route: None
    value._source = ''
    value._task_id = ''
    value._pickup = ''
    value._dropoff = ''
    value._route_nodes = []
    value._current_stop_index = 0
    value._return_home = True
    value._abort_reason = ''
    value._mission_started_wall = 0.0
    value._mission_elapsed = 0.0
    value._status_detail = 'goreve hazir'
    value._next_node = ''
    value._assign = FakeAssignClient()
    value.events = []
    value.starts = 0
    value._event = lambda name, **fields: value.events.append((name, fields))

    def run_once():
        value.starts += 1

    value._start_mission_thread = run_once
    return value


@pytest.mark.parametrize(
    ('attribute', 'blocked_value'),
    (
        ('_plc_auto_start', False),
        ('_default_source', 'mock_plc'),
        ('_plc_connected', False),
        ('_busy', True),
    ),
)
def test_disabled_mock_disconnected_or_busy_never_requests_assignment(
    manager, attribute, blocked_value
):
    setattr(manager, attribute, blocked_value)

    manager._poll_plc_auto_start()

    assert manager._assign.calls == []
    assert manager.starts == 0


def test_control_wait_is_nonfatal_and_remains_idle(manager):
    manager._poll_plc_auto_start()
    assert len(manager._assign.calls) == 1

    manager._assign.calls[0][1].set_result(_reply(False))

    assert manager._state == RobotStatus.STATE_IDLE
    assert not manager._busy
    assert not manager._plc_assign_inflight
    assert manager.starts == 0
    assert manager.events == []


def test_fake_service_wait_then_run_sequence_starts_once(manager):
    """Stay idle on no assignment, then start on the next valid response."""
    manager._poll_plc_auto_start()
    manager._assign.calls[0][1].set_result(_reply(False))
    assert manager.starts == 0

    manager._poll_plc_auto_start()
    manager._assign.calls[1][1].set_result(_reply(True))

    assert manager.starts == 1
    assert manager._task_id == 'plc-task-1'


def test_fresh_assignment_is_reserved_and_started_exactly_once(manager):
    manager._poll_plc_auto_start()
    manager._assign.calls[0][1].set_result(_reply(True))

    assert manager._task_id == 'plc-task-1'
    assert manager._pickup == 'A1'
    assert manager._dropoff == 'B3'
    assert manager._source == 'plc'
    assert manager._busy
    assert manager._running
    assert manager.starts == 1
    assert manager._known_task_ids == {'plc-task-1'}


def test_field_not_ready_waits_then_starts_after_field_becomes_ready(manager):
    manager._active_field_ready = False
    manager._poll_plc_auto_start()
    assert manager._assign.calls == []
    assert manager._state == RobotStatus.STATE_IDLE

    manager._active_field_ready = True
    manager._poll_plc_auto_start()
    manager._assign.calls[0][1].set_result(_reply(True))

    assert manager.starts == 1


@pytest.mark.parametrize('unhealthy', ('localization', 'base', 'safety'))
def test_unhealthy_localization_base_or_safety_blocks_start(manager, unhealthy):
    if unhealthy == 'localization':
        manager._localization_health = lambda: LocalizationHealth(
            False, 'AMCL hazir degil')
    elif unhealthy == 'base':
        manager._base_communication_healthy = lambda: False
    else:
        manager._safety_reset.ready = False

    manager._poll_plc_auto_start()

    assert manager._assign.calls == []
    assert manager.starts == 0


def test_same_task_id_cannot_start_again_after_completion(manager):
    manager._poll_plc_auto_start()
    manager._assign.calls[0][1].set_result(_reply(True))
    assert manager.starts == 1

    # Model the existing mission-finally lifecycle while retaining known IDs.
    manager._busy = False
    manager._running = False
    manager._state = RobotStatus.STATE_IDLE
    manager._poll_plc_auto_start()
    manager._assign.calls[1][1].set_result(_reply(True))

    assert manager.starts == 1
    assert manager._known_task_ids == {'plc-task-1'}


def test_auto_start_and_manual_start_share_one_inflight_claim(manager):
    manager._poll_plc_auto_start()
    assert len(manager._assign.calls) == 1

    # This is the common core used by /mission/start. It loses the race while
    # the asynchronous auto-start request owns the single in-flight claim.
    error = manager._request_plc_assignment_and_reserve()
    assert error == 'PLC gorev istegi devam ediyor'

    manager._assign.calls[0][1].set_result(_reply(True))
    assert len(manager._assign.calls) == 1
    assert manager.starts == 1


def test_readiness_loss_after_request_prevents_movement(manager):
    manager._poll_plc_auto_start()
    manager._active_field_ready = False

    manager._assign.calls[0][1].set_result(_reply(True))

    assert manager.starts == 0
    assert not manager._busy
    assert manager._state == RobotStatus.STATE_IDLE


def test_late_response_from_timed_out_request_is_ignored(manager):
    manager._poll_plc_auto_start()
    old_future = manager._assign.calls[0][1]
    manager._plc_assign_started -= 6.0

    manager._poll_plc_auto_start()
    assert old_future.cancelled
    old_future.set_result(_reply(True))

    assert manager.starts == 0
    assert manager._known_task_ids == set()
