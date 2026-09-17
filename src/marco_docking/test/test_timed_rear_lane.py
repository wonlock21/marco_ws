"""Unit tests for the production rear-lane docking adapter."""

import math
import threading
import time
from types import SimpleNamespace

from geometry_msgs.msg import Twist
import pytest
from std_msgs.msg import Bool

from marco_docking import dock_server
from marco_docking.dock_server import DockServer
from marco_docking.dock_server import reverse_lane_command
from marco_msgs.action import DockToStation


def test_reverse_lane_command_scales_both_for_linear_limit():
    lane = Twist()
    lane.linear.x = 0.125
    lane.angular.z = 0.20

    command = reverse_lane_command(lane, 1.0, 0.05, 0.40)

    assert command.linear.x == pytest.approx(-0.05)
    assert command.angular.z == pytest.approx(0.08)


def test_reverse_lane_command_scales_both_for_angular_limit():
    lane = Twist()
    lane.linear.x = 0.04
    lane.angular.z = 0.80

    command = reverse_lane_command(lane, 1.0, 0.05, 0.40)

    assert command.linear.x == pytest.approx(-0.02)
    assert command.angular.z == pytest.approx(0.40)


def test_reverse_lane_command_does_not_scale_within_limits():
    lane = Twist()
    lane.linear.x = 0.04
    lane.angular.z = 0.20

    command = reverse_lane_command(lane, 1.0, 0.05, 0.40)

    assert command.linear.x == pytest.approx(-0.04)
    assert command.angular.z == pytest.approx(0.20)


def test_reverse_lane_command_preserves_curvature_ratio():
    lane = Twist()
    lane.linear.x = 0.125
    lane.angular.z = 0.20

    command = reverse_lane_command(lane, 1.0, 0.05, 0.40)

    raw_linear = -abs(lane.linear.x)
    raw_angular = lane.angular.z
    assert command.linear.x / command.angular.z == pytest.approx(
        raw_linear / raw_angular
    )


def test_reverse_lane_command_preserves_negative_steering():
    lane = Twist()
    lane.linear.x = -0.062
    lane.angular.z = -0.150

    command = reverse_lane_command(lane, 1.0, 0.05, 0.40)

    assert command.linear.x == pytest.approx(-0.05)
    assert command.angular.z == pytest.approx(-0.12096774193548387)


def test_reverse_lane_command_rejects_non_finite_input():
    lane = Twist()
    lane.linear.x = math.nan

    with pytest.raises(ValueError, match="non-finite"):
        reverse_lane_command(lane, 1.0, 0.05, 0.40)


class _Publisher:

    def __init__(self, callback=None):
        self.messages = []
        self._callback = callback

    def publish(self, message):
        self.messages.append(message)
        if self._callback is not None:
            self._callback(message)


class _GoalHandle:

    def __init__(self, duration):
        self.request = SimpleNamespace(
            line_follow_duration_s=duration,
            reverse_motion=True,
            camera_source='rear_camera',
            approach_type=DockToStation.Goal.APPROACH_PICKUP,
            timeout=0.0,
        )
        self.is_cancel_requested = False
        self.state = ''
        self.feedback = []

    def publish_feedback(self, feedback):
        self.feedback.append(feedback)

    def succeed(self):
        self.state = 'succeeded'

    def abort(self):
        self.state = 'aborted'

    def canceled(self):
        self.state = 'canceled'


def _rear_lane_server(
    timeout, publish_fresh_end, zero_without_end=False, zero_grace=0.01
):
    server = DockServer.__new__(DockServer)
    server._p = {
        'control_rate_hz': 1000.0,
        'reverse_docking_timeout_s': timeout,
        'activation_timeout_s': 0.02,
        'camera_timeout_s': 1.0,
        'lane_active_timeout_s': 1.0,
        'lane_command_timeout_s': 1.0,
        'zero_command_timeout_s': 0.01,
        'lane_end_zero_grace_s': zero_grace,
        'load_detected_debounce_s': 0.075,
        'load_detected_freshness_s': 0.25,
        'base_health_timeout_s': 0.50,
        'odom_timeout_s': 1.0,
        'stop_timeout_s': 0.05,
        'stop_settle_s': 0.0,
        'stop_linear_tolerance': 0.01,
        'stop_angular_tolerance': 0.03,
        'reverse_angular_sign': 1.0,
        'max_linear_vel': 0.05,
        'max_angular_vel': 0.40,
    }
    server._estop = False
    server._manual = False
    server._obstacle = False
    server._communication_ok = True
    server._communication_wall = time.monotonic()
    server._load_detected = False
    server._load_detected_wall = time.monotonic()
    server._load_detected_sequence = 1
    server._load_true_since = 0.0
    server._load_true_samples = 0
    server._load_lock = threading.Lock()
    server._lane_active = False
    server._lane_active_wall = 0.0
    server._lane_end_wall = 0.0
    server._camera_wall = 0.0
    server._lane_command = Twist()
    server._lane_command_wall = 0.0
    server._odom_wall = 0.0
    server._linear_speed = 0.02
    server._angular_speed = 0.0
    server._busy = True
    server._busy_lock = threading.Lock()
    terminal_command_sent = False

    def task_command(message):
        now = time.monotonic()
        if message.data == 'START_LANE':
            server._camera_wall = now
            server._lane_active = True
            server._lane_active_wall = now
            server._lane_command = Twist()
            server._lane_command.linear.x = 0.05
            server._lane_command.angular.z = 0.10
            server._lane_command_wall = now
        elif message.data == 'STOP':
            server._lane_active = False
            server._lane_active_wall = now
            server._lane_command = Twist()
            server._lane_command_wall = now
            server._odom_wall = now
            server._linear_speed = 0.0
            server._angular_speed = 0.0

    def dock_command(message):
        nonlocal terminal_command_sent
        if (
            (publish_fresh_end or zero_without_end)
            and not terminal_command_sent
            and abs(float(message.linear.x)) > 0.0
        ):
            terminal_command_sent = True
            # The real controller zeros its command immediately before the
            # end event; that zero must be treated as normal completion.
            server._lane_command = Twist()
            server._lane_command_wall = time.monotonic()
            server._test_zero_started_wall = time.monotonic()
            if publish_fresh_end:
                server._on_lane_end(Bool(data=True))

    server._task_pub = _Publisher(task_command)
    server._pub = _Publisher(dock_command)
    server._test_zero_started_wall = None
    return server


class _FakeClock:

    def __init__(self):
        self.now = 100.0
        self.on_sleep = None

    def monotonic(self):
        return self.now

    def sleep(self, duration):
        self.now += float(duration)
        if self.on_sleep is not None:
            self.on_sleep(self.now)


def _run_zero_grace_scenario(
    monkeypatch, *, lane_end_after=None, estop_after=None,
    obstacle_after=None,
):
    clock = _FakeClock()
    monkeypatch.setattr(dock_server.time, 'monotonic', clock.monotonic)
    monkeypatch.setattr(dock_server.time, 'sleep', clock.sleep)
    monkeypatch.setattr(dock_server.rclpy, 'ok', lambda: True)
    server = _rear_lane_server(
        3.0, publish_fresh_end=False, zero_without_end=True,
        zero_grace=1.5,
    )
    server._p['control_rate_hz'] = 20.0
    server._p['activation_timeout_s'] = 0.2
    server._p['camera_timeout_s'] = 10.0
    server._p['lane_active_timeout_s'] = 10.0
    server._p['lane_command_timeout_s'] = 10.0
    event_sent = False

    def update_inputs(now):
        nonlocal event_sent
        zero_started = server._test_zero_started_wall
        if zero_started is None:
            return
        server._camera_wall = now
        server._lane_active = True
        server._lane_active_wall = now
        server._lane_command_wall = now
        elapsed = now - zero_started
        if lane_end_after is not None and elapsed >= lane_end_after:
            if not event_sent:
                event_sent = True
                server._on_lane_end(Bool(data=True))
        if estop_after is not None and elapsed >= estop_after:
            server._estop = True
        if obstacle_after is not None and elapsed >= obstacle_after:
            server._obstacle = True

    clock.on_sleep = update_inputs
    handle = _GoalHandle(duration=math.nan)
    result = server._execute(handle)
    return clock, server, handle, result


def _commands_after_first_motion(server):
    messages = server._pub.messages
    first_motion = next(
        index for index, message in enumerate(messages)
        if abs(float(message.linear.x)) > 0.0
        or abs(float(message.angular.z)) > 0.0
    )
    return messages[first_motion + 1:]


def test_fresh_lane_end_stops_and_succeeds_despite_zero_lane_command(
    monkeypatch,
):
    monkeypatch.setattr(dock_server.rclpy, 'ok', lambda: True)
    server = _rear_lane_server(0.1, publish_fresh_end=True)
    handle = _GoalHandle(duration=math.nan)

    result = server._execute(handle)

    assert handle.state == 'succeeded'
    assert result.result_code == DockToStation.Result.RESULT_OK
    assert 'fresh lane-end' in result.message
    assert any(
        message.data == 'STOP' for message in server._task_pub.messages
    )
    assert server._pub.messages[-1].linear.x == 0.0
    assert server._pub.messages[-1].angular.z == 0.0
    assert server._busy is False


def test_stale_lane_end_and_short_duration_cannot_complete_docking(
    monkeypatch,
):
    monkeypatch.setattr(dock_server.rclpy, 'ok', lambda: True)
    server = _rear_lane_server(0.02, publish_fresh_end=False)
    server._lane_end_wall = time.monotonic()
    handle = _GoalHandle(duration=0.001)

    result = server._execute(handle)

    assert handle.state == 'aborted'
    assert result.result_code == DockToStation.Result.RESULT_TIMEOUT
    assert 'lane-end' in result.message
    assert server._pub.messages[-1].linear.x == 0.0
    assert server._pub.messages[-1].angular.z == 0.0


def test_zero_lane_command_without_fresh_end_remains_lane_loss(monkeypatch):
    monkeypatch.setattr(dock_server.rclpy, 'ok', lambda: True)
    server = _rear_lane_server(
        0.1, publish_fresh_end=False, zero_without_end=True
    )
    handle = _GoalHandle(duration=0.001)

    result = server._execute(handle)

    assert handle.state == 'aborted'
    assert result.result_code == DockToStation.Result.RESULT_LANE_LOST
    assert 'serit kaybi' in result.message


def test_zero_command_then_fresh_lane_end_within_grace_succeeds(monkeypatch):
    clock, server, handle, result = _run_zero_grace_scenario(
        monkeypatch, lane_end_after=0.8,
    )

    assert handle.state == 'succeeded'
    assert result.result_code == DockToStation.Result.RESULT_OK
    assert clock.now - server._test_zero_started_wall >= 0.8
    assert clock.now - server._test_zero_started_wall < 1.5


def test_zero_command_without_lane_end_fails_when_grace_expires(monkeypatch):
    clock, server, handle, result = _run_zero_grace_scenario(monkeypatch)

    assert handle.state == 'aborted'
    assert result.result_code == DockToStation.Result.RESULT_LANE_LOST
    assert clock.now - server._test_zero_started_wall >= 1.5
    assert 'zero grace' in result.message


def test_dock_output_remains_zero_through_lane_end_grace(monkeypatch):
    _, server, _, result = _run_zero_grace_scenario(
        monkeypatch, lane_end_after=0.8,
    )

    assert result.result_code == DockToStation.Result.RESULT_OK
    grace_commands = _commands_after_first_motion(server)
    assert grace_commands
    assert all(
        message.linear.x == 0.0 and message.angular.z == 0.0
        for message in grace_commands
    )


def test_estop_during_lane_end_grace_aborts_immediately(monkeypatch):
    clock, server, handle, result = _run_zero_grace_scenario(
        monkeypatch, estop_after=0.2,
    )

    assert handle.state == 'aborted'
    assert result.result_code == DockToStation.Result.RESULT_ABORTED
    assert clock.now - server._test_zero_started_wall < 1.5
    assert 'e-stop' in result.message


def test_obstacle_during_lane_end_grace_aborts_immediately(monkeypatch):
    clock, server, handle, result = _run_zero_grace_scenario(
        monkeypatch, obstacle_after=0.2,
    )

    assert handle.state == 'aborted'
    assert result.result_code == DockToStation.Result.RESULT_OBSTACLE
    assert clock.now - server._test_zero_started_wall < 1.5
    assert 'engel' in result.message


def _run_load_scenario(
    monkeypatch, *, dropoff=False, glitch=False, stuck_high=False,
    simultaneous_lane_end=False,
):
    clock = _FakeClock()
    monkeypatch.setattr(dock_server.time, 'monotonic', clock.monotonic)
    monkeypatch.setattr(dock_server.time, 'sleep', clock.sleep)
    monkeypatch.setattr(dock_server.rclpy, 'ok', lambda: True)
    server = _rear_lane_server(1.0, publish_fresh_end=False)
    server._p['control_rate_hz'] = 20.0
    server._p['stop_timeout_s'] = 1.0
    server._p['stop_settle_s'] = 0.0
    server._p['activation_timeout_s'] = 0.2
    server._communication_wall = clock.now
    server._load_detected_wall = clock.now
    if stuck_high:
        server._on_load_detected(Bool(data=True))
    started = clock.now
    lane_end_sent = False

    def update_inputs(now):
        nonlocal lane_end_sent
        server._camera_wall = now
        server._lane_active_wall = now
        server._lane_command_wall = now
        elapsed = now - started
        if stuck_high:
            server._on_load_detected(Bool(data=True))
        elif glitch:
            if 0.05 <= elapsed < 0.10:
                server._on_load_detected(Bool(data=True))
            elif elapsed >= 0.10:
                server._on_load_detected(Bool(data=False))
        elif elapsed >= 0.05:
            server._on_load_detected(Bool(data=True))
        lane_end_at = 0.15 if simultaneous_lane_end else 0.20
        if (
            (dropoff or glitch or stuck_high or simultaneous_lane_end)
            and elapsed >= lane_end_at
            and not lane_end_sent
        ):
            lane_end_sent = True
            server._on_lane_end(Bool(data=True))

    clock.on_sleep = update_inputs
    handle = _GoalHandle(duration=math.nan)
    if dropoff:
        handle.request.approach_type = DockToStation.Goal.APPROACH_DROPOFF
    result = server._execute(handle)
    return clock, server, handle, result


def test_fresh_debounced_load_stops_and_reports_physical_completion(
    monkeypatch,
):
    _, server, handle, result = _run_load_scenario(monkeypatch)

    assert handle.state == 'succeeded'
    assert result.success
    assert result.result_code == DockToStation.Result.RESULT_LOAD_DETECTED
    assert 'fiziksel yuk temasi' in result.message
    assert any(msg.data == 'STOP' for msg in server._task_pub.messages)
    assert server._pub.messages[-1].linear.x == 0.0


def test_load_completion_waits_for_measured_stop(monkeypatch):
    clock = _FakeClock()
    monkeypatch.setattr(dock_server.time, 'monotonic', clock.monotonic)
    monkeypatch.setattr(dock_server.time, 'sleep', clock.sleep)
    monkeypatch.setattr(dock_server.rclpy, 'ok', lambda: True)
    server = _rear_lane_server(1.0, publish_fresh_end=False)
    server._p['control_rate_hz'] = 20.0
    server._p['stop_timeout_s'] = 1.0
    server._p['stop_settle_s'] = 0.0
    server._communication_wall = clock.now
    server._load_detected_wall = clock.now
    started = clock.now
    original_task_callback = server._task_pub._callback

    def delayed_stop(message):
        original_task_callback(message)
        if message.data == 'STOP' and clock.now - started < 0.35:
            server._odom_wall = clock.now
            server._linear_speed = 0.02

    server._task_pub._callback = delayed_stop

    def update_inputs(now):
        server._camera_wall = now
        server._lane_active_wall = now
        server._lane_command_wall = now
        if now - started >= 0.05:
            server._on_load_detected(Bool(data=True))

    clock.on_sleep = update_inputs
    result = server._execute(_GoalHandle(duration=math.nan))

    assert result.result_code == DockToStation.Result.RESULT_LOAD_DETECTED
    assert clock.now - started >= 0.35


def test_single_load_glitch_does_not_complete_before_visual_lane_end(
    monkeypatch,
):
    _, _, _, result = _run_load_scenario(monkeypatch, glitch=True)

    assert result.result_code == DockToStation.Result.RESULT_OK
    assert 'lane-end' in result.message


def test_pre_session_stuck_high_does_not_complete_and_does_not_block_lane_end(
    monkeypatch,
):
    _, _, _, result = _run_load_scenario(monkeypatch, stuck_high=True)

    assert result.result_code == DockToStation.Result.RESULT_OK


def test_dropoff_ignores_fresh_debounced_load(monkeypatch):
    _, _, _, result = _run_load_scenario(monkeypatch, dropoff=True)

    assert result.result_code == DockToStation.Result.RESULT_OK


def test_simultaneous_lane_end_and_load_has_one_physical_completion(
    monkeypatch,
):
    _, _, handle, result = _run_load_scenario(
        monkeypatch, simultaneous_lane_end=True)

    assert handle.state == 'succeeded'
    assert result.result_code == DockToStation.Result.RESULT_LOAD_DETECTED


@pytest.mark.parametrize('unsafe_state', ['manual', 'communication'])
def test_load_does_not_bypass_base_safety(monkeypatch, unsafe_state):
    clock = _FakeClock()
    monkeypatch.setattr(dock_server.time, 'monotonic', clock.monotonic)
    server = _rear_lane_server(1.0, publish_fresh_end=False)
    server._communication_wall = clock.now
    server._load_detected_wall = clock.now
    session = server._new_load_session(clock.now)
    clock.now += 0.05
    server._on_load_detected(Bool(data=True))
    clock.now += 0.08
    server._on_load_detected(Bool(data=True))
    if unsafe_state == 'manual':
        server._manual = True
    else:
        server._communication_ok = False

    assert server._load_trigger_ready(session, clock.now) is False
