"""Fail-closed behavior tests for the production STM32 lift action."""

import math
import time
from types import SimpleNamespace

import pytest
import rclpy
from rclpy.action import GoalResponse
from rclpy.parameter import Parameter

from marco_base import protocol as p
from marco_base.base_driver import BaseDriver
from marco_msgs.action import LiftLoad


class RecordingTransport:
    def __init__(self):
        self.writes = []

    def write(self, data):
        self.writes.append((time.monotonic(), data))

    def read(self):
        return b""

    def close(self):
        pass


class FakeGoalHandle:
    def __init__(self, request, *, cancel=False, on_feedback=None):
        self.request = request
        self.is_cancel_requested = cancel
        self.on_feedback = on_feedback
        self.terminal = None
        self.feedback = []

    def abort(self):
        self.terminal = "aborted"

    def canceled(self):
        self.terminal = "canceled"

    def succeed(self):
        self.terminal = "succeeded"

    def publish_feedback(self, feedback):
        self.feedback.append(feedback)
        if self.on_feedback is not None:
            self.on_feedback()


def _goal(
    timeout=0.3,
    command=LiftLoad.Goal.COMMAND_PICKUP,
    station="A1",
):
    return SimpleNamespace(
        command=command,
        station_id=station,
        timeout=timeout,
    )


def _status(flags=p.StatusFlag(0)):
    return p.StatusFrame(0, flags, 12600, 0, 0, 30, 0)


def _fork_records(transport):
    records = []
    for written_at, raw in transport.writes:
        for msg_id, payload in p.FrameParser().feed(raw):
            if msg_id is p.MsgId.CMD_FORK:
                action, lease_ms = p.decode_fork(payload)
                records.append((written_at, action, lease_ms))
    return records


def _fork_actions(transport):
    return [record[1] for record in _fork_records(transport)]


def _collapsed_fork_actions(transport):
    collapsed = []
    for action in _fork_actions(transport):
        if not collapsed or action is not collapsed[-1]:
            collapsed.append(action)
    return collapsed


def _healthy(node, flags=p.StatusFlag(0)):
    now = time.monotonic()
    node._status = _status(flags)
    node._last_valid_frame_wall = now
    node._last_status_wall = now


@pytest.fixture
def make_node():
    rclpy.init()
    nodes = []

    def factory(
        *,
        pickup=0.04,
        dropoff=0.04,
        tilt_pickup=0.04,
        tilt_dropoff=0.04,
        communication=0.2,
    ):
        node = BaseDriver(parameter_overrides=[
            Parameter("use_fake_hardware", value=True),
            Parameter("wheel_measurement_log_enabled", value=False),
            Parameter("lift_action_server_enabled", value=True),
            Parameter("communication_timeout", value=communication),
            Parameter("lift_pickup_duration_s", value=pickup),
            Parameter("lift_dropoff_duration_s", value=dropoff),
            Parameter("tilt_pickup_duration_s", value=tilt_pickup),
            Parameter("tilt_dropoff_duration_s", value=tilt_dropoff),
        ])
        node._transport = RecordingTransport()
        nodes.append(node)
        return node

    yield factory

    for node in nodes:
        node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


def _inject_status_on_phase(node, handle, phase, flags):
    def update():
        if handle.feedback[-1].phase == phase:
            _healthy(node, flags)

    handle.on_feedback = update


def test_load_detected_flag_round_trips_without_layout_change():
    flags = p.StatusFlag.LOAD_DETECTED | p.StatusFlag.LIMIT_SWITCH_UP
    encoded = p.encode_status(_status(flags))
    frames = list(p.FrameParser().feed(encoded))

    assert len(frames) == 1
    assert len(frames[0][1]) == p.STATUS_PAYLOAD_LEN
    decoded = p.decode_status(frames[0][1])
    assert p.StatusFlag.LOAD_DETECTED in decoded.flags
    assert p.StatusFlag.LIMIT_SWITCH_UP in decoded.flags


def test_fork_action_wire_values_are_stable_and_extended():
    expected = (
        (p.ForkAction.STOP, 0),
        (p.ForkAction.UP, 1),
        (p.ForkAction.DOWN, 2),
        (p.ForkAction.TILT_UP, 3),
        (p.ForkAction.TILT_DOWN, 4),
    )
    for action, wire_value in expected:
        encoded = p.encode_fork(action, timeout_ms=500)
        _, payload = list(p.FrameParser().feed(encoded))[0]
        decoded, timeout_ms = p.decode_fork(payload)
        assert int(action) == wire_value
        assert decoded is action
        assert timeout_ms == 500


def test_communication_loss_estop_and_manual_reject_new_goal(make_node):
    node = make_node()

    assert node._lift_goal_callback(_goal()) == GoalResponse.REJECT
    _healthy(node, p.StatusFlag.ESTOP_ACTIVE)
    assert node._lift_goal_callback(_goal()) == GoalResponse.REJECT
    _healthy(node, p.StatusFlag.MODE_MANUAL)
    assert node._lift_goal_callback(_goal()) == GoalResponse.REJECT


def test_duplicate_goal_is_rejected(make_node):
    node = make_node()
    _healthy(node)

    assert node._lift_goal_callback(_goal()) == GoalResponse.ACCEPT
    assert node._lift_goal_callback(_goal()) == GoalResponse.REJECT
    node._lift_goal_active = False


def test_pickup_runs_lift_then_fresh_load_then_tilt_and_succeeds(make_node):
    duration = 0.23
    node = make_node(pickup=duration, communication=0.5)
    _healthy(node)
    handle = FakeGoalHandle(_goal(timeout=0.8))
    _inject_status_on_phase(
        node, handle, "verifying_load", p.StatusFlag.LOAD_DETECTED
    )

    result = node._execute_lift(handle)

    records = _fork_records(node._transport)
    up_records = [item for item in records if item[1] is p.ForkAction.UP]
    first_stop = next(item for item in records if item[1] is p.ForkAction.STOP)
    assert len(up_records) >= 2
    assert first_stop[0] - up_records[0][0] >= duration - 0.01
    assert all(0 < item[2] <= 500 for item in up_records)
    assert _collapsed_fork_actions(node._transport) == [
        p.ForkAction.UP,
        p.ForkAction.STOP,
        p.ForkAction.TILT_UP,
        p.ForkAction.STOP,
    ]
    assert _fork_actions(node._transport)[-1] is p.ForkAction.STOP
    assert handle.terminal == "succeeded"
    assert result.success
    assert result.result_code == LiftLoad.Result.RESULT_OK
    assert "verifying_load" in [item.phase for item in handle.feedback]
    assert [feedback.phase for feedback in handle.feedback][-1] == "tilting_up"
    assert all(math.isnan(feedback.position) for feedback in handle.feedback)


def test_early_load_detection_does_not_finish_pickup_early(make_node):
    duration = 0.08
    node = make_node(pickup=duration)
    _healthy(node)
    handle = FakeGoalHandle(_goal())
    early_seen = []

    def update_status():
        phase = handle.feedback[-1].phase
        if phase == "moving_up":
            _healthy(node, p.StatusFlag.LOAD_DETECTED)
            early_seen.append(time.monotonic())
            assert handle.terminal is None
        elif phase == "verifying_load":
            _healthy(node, p.StatusFlag.LOAD_DETECTED)

    handle.on_feedback = update_status
    started = time.monotonic()
    result = node._execute_lift(handle)

    assert early_seen
    assert time.monotonic() - started >= duration - 0.01
    assert handle.terminal == "succeeded"
    assert result.success


def test_pickup_fresh_status_without_load_aborts(make_node):
    node = make_node()
    _healthy(node, p.StatusFlag.LOAD_DETECTED)
    handle = FakeGoalHandle(_goal())
    _inject_status_on_phase(node, handle, "verifying_load", p.StatusFlag(0))

    result = node._execute_lift(handle)

    assert handle.terminal == "aborted"
    assert not result.success
    assert result.result_code == LiftLoad.Result.RESULT_HARDWARE_FAULT
    assert result.message == "pickup tamamlandi ancak yuk algilanmadi"
    assert p.ForkAction.TILT_UP not in _fork_actions(node._transport)
    assert _fork_actions(node._transport)[-1] is p.ForkAction.STOP


def test_stale_preexisting_load_cannot_succeed(make_node):
    node = make_node(pickup=0.03, communication=0.08)
    _healthy(node, p.StatusFlag.LOAD_DETECTED)
    handle = FakeGoalHandle(_goal(timeout=0.3))

    result = node._execute_lift(handle)

    assert handle.terminal == "aborted"
    assert not result.success
    assert result.result_code == LiftLoad.Result.RESULT_HARDWARE_FAULT
    assert "fresh STM32 status gelmedi" in result.message
    assert p.ForkAction.TILT_UP not in _fork_actions(node._transport)
    assert _fork_actions(node._transport)[-1] is p.ForkAction.STOP


@pytest.mark.parametrize(
    "flags", (p.StatusFlag(0), p.StatusFlag.LOAD_DETECTED)
)
def test_dropoff_stops_after_duration_and_ignores_load_switch(make_node, flags):
    duration = 0.05
    node = make_node(dropoff=duration)
    _healthy(node, flags)
    handle = FakeGoalHandle(_goal(
        command=LiftLoad.Goal.COMMAND_DROPOFF,
        station="B1",
    ))
    started = time.monotonic()

    result = node._execute_lift(handle)

    actions = _fork_actions(node._transport)
    assert time.monotonic() - started >= duration - 0.01
    assert p.ForkAction.DOWN in actions
    assert _collapsed_fork_actions(node._transport) == [
        p.ForkAction.TILT_DOWN,
        p.ForkAction.STOP,
        p.ForkAction.DOWN,
        p.ForkAction.STOP,
    ]
    assert actions[-1] is p.ForkAction.STOP
    assert handle.terminal == "succeeded"
    assert result.success


@pytest.mark.parametrize(
    ("command", "parameter_name"),
    (
        (LiftLoad.Goal.COMMAND_PICKUP, "lift_pickup_duration_s"),
        (LiftLoad.Goal.COMMAND_DROPOFF, "lift_dropoff_duration_s"),
    ),
)
def test_unconfigured_duration_rejects_without_motion(
    make_node, command, parameter_name
):
    node = make_node(pickup=0.0, dropoff=0.0)
    _healthy(node)
    goal = _goal(command=command)

    assert node._lift_goal_callback(goal) == GoalResponse.REJECT
    handle = FakeGoalHandle(goal)
    result = node._execute_lift(handle)

    assert handle.terminal == "aborted"
    assert result.message == f"{parameter_name} yapılandırılmamış"
    assert not any(
        action is not p.ForkAction.STOP
        for action in _fork_actions(node._transport)
    )


@pytest.mark.parametrize("duration", (math.nan, math.inf, -0.1))
@pytest.mark.parametrize("parameter_name", ("pickup", "tilt_pickup"))
def test_nonfinite_or_negative_duration_is_rejected(
    make_node, duration, parameter_name
):
    node = make_node(**{parameter_name: duration})
    _healthy(node)

    assert node._lift_goal_callback(_goal()) == GoalResponse.REJECT


def test_duration_must_be_less_than_overall_timeout(make_node):
    node = make_node(pickup=0.06, tilt_pickup=0.04)
    _healthy(node)
    goal = _goal(timeout=0.1)

    assert node._lift_goal_callback(goal) == GoalResponse.REJECT
    handle = FakeGoalHandle(goal)
    result = node._execute_lift(handle)
    assert handle.terminal == "aborted"
    assert "toplam hareket suresi goal.timeout" in result.message
    assert p.ForkAction.UP not in _fork_actions(node._transport)


def test_cancel_sends_stop(make_node):
    node = make_node(pickup=0.1)
    _healthy(node)
    handle = FakeGoalHandle(_goal())
    handle.on_feedback = lambda: setattr(
        handle, "is_cancel_requested", True
    )

    result = node._execute_lift(handle)

    actions = _fork_actions(node._transport)
    assert handle.terminal == "canceled"
    assert not result.success
    assert p.ForkAction.UP in actions
    assert actions[-1] is p.ForkAction.STOP


def test_cancel_during_tilt_phase_sends_stop(make_node):
    node = make_node()
    _healthy(node)
    handle = FakeGoalHandle(_goal())

    def cancel_during_tilt():
        phase = handle.feedback[-1].phase
        if phase == "verifying_load":
            _healthy(node, p.StatusFlag.LOAD_DETECTED)
        elif phase == "tilting_up":
            handle.is_cancel_requested = True

    handle.on_feedback = cancel_during_tilt
    result = node._execute_lift(handle)

    assert handle.terminal == "canceled"
    assert not result.success
    assert p.ForkAction.TILT_UP in _fork_actions(node._transport)
    assert _fork_actions(node._transport)[-1] is p.ForkAction.STOP


def test_estop_during_tilt_phase_aborts_and_sends_stop(make_node):
    node = make_node()
    _healthy(node)
    handle = FakeGoalHandle(_goal())

    def estop_during_tilt():
        phase = handle.feedback[-1].phase
        if phase == "verifying_load":
            _healthy(node, p.StatusFlag.LOAD_DETECTED)
        elif phase == "tilting_up":
            _healthy(node, p.StatusFlag.ESTOP_ACTIVE)

    handle.on_feedback = estop_during_tilt

    result = node._execute_lift(handle)

    assert handle.terminal == "aborted"
    assert not result.success
    assert "e-stop" in result.message
    assert p.ForkAction.TILT_UP in _fork_actions(node._transport)
    assert _fork_actions(node._transport)[-1] is p.ForkAction.STOP


def test_communication_loss_during_tilt_aborts_and_sends_stop(make_node):
    node = make_node(communication=0.1)
    _healthy(node)
    handle = FakeGoalHandle(_goal())

    def lose_communication():
        phase = handle.feedback[-1].phase
        if phase == "verifying_load":
            _healthy(node, p.StatusFlag.LOAD_DETECTED)
        elif phase == "tilting_up":
            stale = time.monotonic() - node.communication_timeout - 0.01
            node._last_valid_frame_wall = stale
            node._last_status_wall = stale

    handle.on_feedback = lose_communication
    result = node._execute_lift(handle)

    assert handle.terminal == "aborted"
    assert not result.success
    assert "iletisimi yok veya bayat" in result.message
    assert p.ForkAction.TILT_UP in _fork_actions(node._transport)
    assert _fork_actions(node._transport)[-1] is p.ForkAction.STOP


def test_overall_timeout_during_tilt_sends_stop(make_node):
    node = make_node(pickup=0.04, communication=0.2)
    _healthy(node)
    handle = FakeGoalHandle(_goal(timeout=0.1))

    def delayed_load_verification():
        if handle.feedback[-1].phase == "verifying_load":
            time.sleep(0.04)
            _healthy(node, p.StatusFlag.LOAD_DETECTED)

    handle.on_feedback = delayed_load_verification

    result = node._execute_lift(handle)

    assert handle.terminal == "aborted"
    assert result.result_code == LiftLoad.Result.RESULT_TIMEOUT
    assert p.ForkAction.TILT_UP in _fork_actions(node._transport)
    assert _fork_actions(node._transport)[-1] is p.ForkAction.STOP


@pytest.mark.parametrize(
    "flags",
    (
        p.StatusFlag.LIMIT_SWITCH_UP,
        p.StatusFlag.LIMIT_SWITCH_DOWN,
        p.StatusFlag.LIMIT_SWITCH_UP | p.StatusFlag.LIMIT_SWITCH_DOWN,
    ),
)
def test_limit_switch_flags_do_not_complete_pickup(make_node, flags):
    node = make_node()
    _healthy(node, flags)
    handle = FakeGoalHandle(_goal())
    _inject_status_on_phase(node, handle, "verifying_load", flags)

    result = node._execute_lift(handle)

    assert handle.terminal == "aborted"
    assert not result.success
    assert result.message == "pickup tamamlandi ancak yuk algilanmadi"
    assert p.ForkAction.UP in _fork_actions(node._transport)
    assert p.ForkAction.TILT_UP not in _fork_actions(node._transport)
