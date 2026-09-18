"""Regression tests for bounded mission UART recovery."""

import math

import pytest
import rclpy
from std_msgs.msg import Bool

from marco_mission.mission_manager import MissionManager


@pytest.fixture
def manager():
    rclpy.init()
    node = MissionManager()
    node._busy = True
    node._running = True
    node._base_communication_ok = True
    node._base_communication_seen = 100.0
    node._base_communication_recovery_timeout = 5.0
    node._base_communication_recovery_stable = 0.5
    events = []
    stops = []
    aborts = []
    node._event = lambda event, **fields: events.append((event, fields))
    node._safe_stop = lambda: stops.append(True)
    node._request_abort = lambda reason, latch: aborts.append((reason, latch))
    node._test_events = events
    node._test_stops = stops
    node._test_aborts = aborts
    yield node
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


def _start_recovery(manager, started=100.0):
    manager._base_communication_ok = False
    manager._base_communication_seen = started
    manager._start_base_communication_recovery(started)
    return started


def _set_communication(manager, value, now):
    manager._base_communication_ok = value
    manager._base_communication_seen = now
    return manager._update_base_communication_recovery(now)


def test_false_busy_starts_recovery_without_immediate_abort(manager):
    manager._base_communication_seen = 0.0

    manager._on_base_communication(Bool(data=False))

    assert manager._base_communication_recovery_started > 0.0
    assert manager._test_aborts == []
    assert manager._test_stops == [True]
    assert manager._test_events[0][0] == (
        'base_communication_recovery_started'
    )


def test_stable_return_clears_recovery_without_abort(manager):
    started = _start_recovery(manager)

    assert _set_communication(manager, True, started + 2.0)
    assert not _set_communication(manager, True, started + 2.5)

    assert manager._base_communication_recovery_started == 0.0
    assert manager._test_aborts == []
    assert manager._test_events[-1][0] == 'base_communication_recovered'
    assert manager._test_events[-1][1]['stable_s'] == pytest.approx(0.5)


def test_short_true_flap_does_not_reset_original_deadline(manager):
    started = _start_recovery(manager)

    assert _set_communication(manager, True, started + 3.0)
    assert _set_communication(manager, False, started + 3.1)
    assert not _set_communication(manager, False, started + 5.0)

    assert manager._test_aborts == [
        ('STM32/UART iletisimi 5 saniye icinde geri gelmedi', True)
    ]
    assert manager._test_events[-1][0] == (
        'base_communication_recovery_failed'
    )


def test_recovered_outage_allows_a_new_independent_window(manager):
    started = _start_recovery(manager)
    _set_communication(manager, True, started + 1.0)
    _set_communication(manager, True, started + 1.5)

    second_started = started + 2.0
    manager._base_communication_ok = False
    manager._base_communication_seen = second_started
    manager._start_base_communication_recovery(second_started)

    assert manager._base_communication_recovery_started == second_started
    started_events = [
        event for event, _ in manager._test_events
        if event == 'base_communication_recovery_started'
    ]
    assert len(started_events) == 2


def test_recovery_pause_is_excluded_from_motion_deadlines(manager):
    started = _start_recovery(manager)
    active_before = manager._mission_active_time(started)
    _set_communication(manager, True, started + 2.0)
    _set_communication(manager, True, started + 2.5)
    active_after = manager._mission_active_time(started + 2.5)

    assert math.isclose(active_after, active_before, abs_tol=1e-9)


def test_estop_and_safety_abort_remain_immediate_during_recovery(manager):
    _start_recovery(manager)

    manager._on_estop(Bool(data=True))
    manager._on_manual(Bool(data=True))
    manager._on_safety_abort(Bool(data=True))

    assert manager._manual
    assert ('e-stop aktif', True) in manager._test_aborts
    assert ('safety abort', True) in manager._test_aborts
