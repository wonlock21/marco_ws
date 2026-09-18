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


class RecordingPublisher:
    def __init__(self):
        self.messages = []

    def publish(self, message):
        self.messages.append(message)


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
        pickup_tilt=0.04,
        dropoff=0.04,
        dropoff_tilt=0.04,
        communication=0.2,
        use_default_durations=False,
    ):
        overrides = [
            Parameter("use_fake_hardware", value=True),
            Parameter("wheel_measurement_log_enabled", value=False),
            Parameter("lift_action_server_enabled", value=True),
            Parameter("communication_timeout", value=communication),
        ]
        if not use_default_durations:
            overrides.extend([
                Parameter("lift_pickup_duration_s", value=pickup),
                Parameter("lift_pickup_tilt_duration_s", value=pickup_tilt),
                Parameter("lift_dropoff_duration_s", value=dropoff),
                Parameter("lift_dropoff_tilt_duration_s", value=dropoff_tilt),
            ])
        node = BaseDriver(parameter_overrides=overrides)
        node._transport = RecordingTransport()
        nodes.append(node)
        return node

    yield factory

    for node in nodes:
        node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


def test_load_detected_flag_round_trips_without_layout_change():
    flags = p.StatusFlag.LOAD_DETECTED | p.StatusFlag.LIMIT_SWITCH_UP
    encoded = p.encode_status(_status(flags))
    frames = list(p.FrameParser().feed(encoded))

    assert len(frames) == 1
    assert len(frames[0][1]) == p.STATUS_PAYLOAD_LEN
    decoded = p.decode_status(frames[0][1])
    assert p.StatusFlag.LOAD_DETECTED in decoded.flags
    assert p.StatusFlag.LIMIT_SWITCH_UP in decoded.flags


def test_load_detected_topic_is_published_only_from_status_frames(make_node):
    node = make_node()
    publisher = RecordingPublisher()
    node._load_detected_pub = publisher

    node._on_status(_status(p.StatusFlag(0)))
    node._on_status(_status(p.StatusFlag.LOAD_DETECTED))
    published_before_health_timer = len(publisher.messages)
    node._publish_communication_health()

    assert [message.data for message in publisher.messages] == [False, True]
    assert len(publisher.messages) == published_before_health_timer


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


def test_lift_duration_parameter_defaults(make_node):
    node = make_node(use_default_durations=True)

    assert node.lift_pickup_duration_s == 15.0
    assert node.lift_pickup_tilt_duration_s == 1.5
    assert node.lift_dropoff_duration_s == 15.0
    assert node.lift_dropoff_tilt_duration_s == 1.5


def test_pickup_runs_lift_then_stop_and_succeeds_without_load(make_node):
    duration = 0.23
    tilt_duration = 0.06
    node = make_node(
        pickup=duration,
        pickup_tilt=tilt_duration,
        communication=0.6,
    )
    _healthy(node)
    handle = FakeGoalHandle(_goal(timeout=0.8))

    result = node._execute_lift(handle)

    records = _fork_records(node._transport)
    up_records = [item for item in records if item[1] is p.ForkAction.UP]
    tilt_records = [
        item for item in records if item[1] is p.ForkAction.TILT_UP
    ]
    first_stop = next(item for item in records if item[1] is p.ForkAction.STOP)
    tilt_stop = next(
        item for item in records
        if item[1] is p.ForkAction.STOP and item[0] > tilt_records[0][0]
    )
    assert len(up_records) >= 2
    assert first_stop[0] - up_records[0][0] >= duration - 0.01
    assert tilt_stop[0] - tilt_records[0][0] >= tilt_duration - 0.01
    assert all(0 < item[2] <= 500 for item in up_records)
    assert all(0 < item[2] <= 500 for item in tilt_records)
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
    assert result.message == "pickup lift sirasi tamamlandi; STOP gonderildi"
    assert p.ForkAction.TILT_UP in _fork_actions(node._transport)
    assert "verifying_load" not in [item.phase for item in handle.feedback]
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

    handle.on_feedback = update_status
    started = time.monotonic()
    result = node._execute_lift(handle)

    assert early_seen
    assert time.monotonic() - started >= duration - 0.01
    assert handle.terminal == "succeeded"
    assert result.success


def test_pickup_succeeds_when_status_has_no_load_detected(make_node):
    node = make_node()
    _healthy(node, p.StatusFlag(0))
    handle = FakeGoalHandle(_goal())

    result = node._execute_lift(handle)

    assert handle.terminal == "succeeded"
    assert result.success
    assert result.result_code == LiftLoad.Result.RESULT_OK
    assert _collapsed_fork_actions(node._transport) == [
        p.ForkAction.UP,
        p.ForkAction.STOP,
        p.ForkAction.TILT_UP,
        p.ForkAction.STOP,
    ]
    assert _fork_actions(node._transport)[-1] is p.ForkAction.STOP


def test_pickup_does_not_require_post_stop_fresh_status(make_node):
    node = make_node(pickup=0.03, pickup_tilt=0.03, communication=0.2)
    _healthy(node)
    handle = FakeGoalHandle(_goal(timeout=0.3))

    result = node._execute_lift(handle)

    assert handle.terminal == "succeeded"
    assert result.success
    assert result.result_code == LiftLoad.Result.RESULT_OK
    assert p.ForkAction.TILT_UP in _fork_actions(node._transport)
    assert _fork_actions(node._transport)[-1] is p.ForkAction.STOP


@pytest.mark.parametrize(
    "flags", (p.StatusFlag(0), p.StatusFlag.LOAD_DETECTED)
)
def test_dropoff_stops_after_duration_and_ignores_load_switch(make_node, flags):
    duration = 0.05
    tilt_duration = 0.03
    node = make_node(dropoff=duration, dropoff_tilt=tilt_duration)
    _healthy(node, flags)
    handle = FakeGoalHandle(_goal(
        command=LiftLoad.Goal.COMMAND_DROPOFF,
        station="B1",
    ))
    started = time.monotonic()

    result = node._execute_lift(handle)

    actions = _fork_actions(node._transport)
    assert time.monotonic() - started >= duration + tilt_duration - 0.02
    assert p.ForkAction.DOWN in actions
    assert _collapsed_fork_actions(node._transport) == [
        p.ForkAction.DOWN,
        p.ForkAction.STOP,
        p.ForkAction.TILT_DOWN,
        p.ForkAction.STOP,
    ]
    assert actions[-1] is p.ForkAction.STOP
    assert p.ForkAction.TILT_DOWN in actions
    assert handle.terminal == "succeeded"
    assert result.success
    assert result.message == "dropoff lift sirasi tamamlandi; STOP gonderildi"


@pytest.mark.parametrize(
    ("command", "tilt_parameter", "tilt_action", "motion_action"),
    (
        (
            LiftLoad.Goal.COMMAND_PICKUP,
            "pickup_tilt",
            p.ForkAction.TILT_UP,
            p.ForkAction.UP,
        ),
        (
            LiftLoad.Goal.COMMAND_DROPOFF,
            "dropoff_tilt",
            p.ForkAction.TILT_DOWN,
            p.ForkAction.DOWN,
        ),
    ),
)
def test_zero_tilt_duration_skips_stage_safely(
    make_node, command, tilt_parameter, tilt_action, motion_action
):
    node = make_node(**{tilt_parameter: 0.0})
    _healthy(node)
    goal = _goal(command=command)

    assert node._lift_goal_callback(goal) == GoalResponse.ACCEPT
    handle = FakeGoalHandle(goal)
    result = node._execute_lift(handle)

    assert handle.terminal == "succeeded"
    assert result.success
    assert tilt_action not in _fork_actions(node._transport)
    assert _collapsed_fork_actions(node._transport) == [
        motion_action,
        p.ForkAction.STOP,
    ]


@pytest.mark.parametrize("duration", (math.nan, math.inf, -0.1))
@pytest.mark.parametrize(
    ("parameter_name", "command"),
    (
        ("pickup", LiftLoad.Goal.COMMAND_PICKUP),
        ("pickup_tilt", LiftLoad.Goal.COMMAND_PICKUP),
        ("dropoff", LiftLoad.Goal.COMMAND_DROPOFF),
        ("dropoff_tilt", LiftLoad.Goal.COMMAND_DROPOFF),
    ),
)
def test_nonfinite_or_negative_duration_is_rejected(
    make_node, duration, parameter_name, command
):
    node = make_node(**{parameter_name: duration})
    _healthy(node)

    assert node._lift_goal_callback(_goal(command=command)) == GoalResponse.REJECT


def test_duration_must_be_less_than_overall_timeout(make_node):
    node = make_node(pickup=0.06, pickup_tilt=0.04)
    _healthy(node)
    goal = _goal(timeout=0.1)

    assert node._lift_goal_callback(goal) == GoalResponse.REJECT
    handle = FakeGoalHandle(goal)
    result = node._execute_lift(handle)
    assert handle.terminal == "aborted"
    assert "toplam hareket suresi goal.timeout" in result.message
    assert p.ForkAction.UP not in _fork_actions(node._transport)


@pytest.mark.parametrize(
    ("command", "cancel_phase", "expected_action"),
    (
        (
            LiftLoad.Goal.COMMAND_PICKUP,
            "moving_up",
            p.ForkAction.UP,
        ),
        (
            LiftLoad.Goal.COMMAND_PICKUP,
            "tilting_up",
            p.ForkAction.TILT_UP,
        ),
        (
            LiftLoad.Goal.COMMAND_DROPOFF,
            "moving_down",
            p.ForkAction.DOWN,
        ),
        (
            LiftLoad.Goal.COMMAND_DROPOFF,
            "tilting_down",
            p.ForkAction.TILT_DOWN,
        ),
    ),
)
def test_cancel_during_each_stage_sends_stop_without_success(
    make_node, command, cancel_phase, expected_action
):
    node = make_node()
    _healthy(node)
    handle = FakeGoalHandle(_goal(command=command))

    def cancel_during_target_stage():
        if handle.feedback[-1].phase == cancel_phase:
            handle.is_cancel_requested = True

    handle.on_feedback = cancel_during_target_stage
    result = node._execute_lift(handle)

    assert handle.terminal == "canceled"
    assert not result.success
    assert result.result_code != LiftLoad.Result.RESULT_OK
    assert expected_action in _fork_actions(node._transport)
    assert _fork_actions(node._transport)[-1] is p.ForkAction.STOP


@pytest.mark.parametrize(
    ("flag", "message"),
    (
        (p.StatusFlag.ESTOP_ACTIVE, "e-stop"),
        (p.StatusFlag.MODE_MANUAL, "manuel mod"),
    ),
)
def test_safety_failure_during_lift_aborts_and_sends_stop(
    make_node, flag, message
):
    node = make_node()
    _healthy(node)
    handle = FakeGoalHandle(_goal())

    def block_during_lift():
        if handle.feedback[-1].phase == "moving_up":
            _healthy(node, flag)

    handle.on_feedback = block_during_lift

    result = node._execute_lift(handle)

    assert handle.terminal == "aborted"
    assert not result.success
    assert message in result.message
    assert p.ForkAction.UP in _fork_actions(node._transport)
    assert _fork_actions(node._transport)[-1] is p.ForkAction.STOP


@pytest.mark.parametrize(
    ("command", "failure_phase", "expected_action"),
    (
        (
            LiftLoad.Goal.COMMAND_PICKUP,
            "moving_up",
            p.ForkAction.UP,
        ),
        (
            LiftLoad.Goal.COMMAND_PICKUP,
            "tilting_up",
            p.ForkAction.TILT_UP,
        ),
        (
            LiftLoad.Goal.COMMAND_DROPOFF,
            "moving_down",
            p.ForkAction.DOWN,
        ),
        (
            LiftLoad.Goal.COMMAND_DROPOFF,
            "tilting_down",
            p.ForkAction.TILT_DOWN,
        ),
    ),
)
def test_communication_loss_during_each_stage_aborts_and_sends_stop(
    make_node, command, failure_phase, expected_action
):
    node = make_node(communication=0.3)
    _healthy(node)
    handle = FakeGoalHandle(_goal(command=command))

    def lose_communication():
        if handle.feedback[-1].phase == failure_phase:
            stale = time.monotonic() - node.communication_timeout - 0.01
            node._last_valid_frame_wall = stale
            node._last_status_wall = stale

    handle.on_feedback = lose_communication
    result = node._execute_lift(handle)

    assert handle.terminal == "aborted"
    assert not result.success
    assert "iletisimi yok veya bayat" in result.message
    assert expected_action in _fork_actions(node._transport)
    assert _fork_actions(node._transport)[-1] is p.ForkAction.STOP


def test_pickup_never_enters_load_verification_phase(make_node):
    node = make_node(pickup=0.04)
    _healthy(node)
    handle = FakeGoalHandle(_goal())

    result = node._execute_lift(handle)

    assert handle.terminal == "succeeded"
    assert result.result_code == LiftLoad.Result.RESULT_OK
    assert "verifying_load" not in [item.phase for item in handle.feedback]
    assert p.ForkAction.UP in _fork_actions(node._transport)
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
def test_pickup_success_does_not_depend_on_limit_switch_flags(make_node, flags):
    node = make_node()
    _healthy(node, flags)
    handle = FakeGoalHandle(_goal())

    result = node._execute_lift(handle)

    assert handle.terminal == "succeeded"
    assert result.success
    assert result.result_code == LiftLoad.Result.RESULT_OK
    assert p.ForkAction.UP in _fork_actions(node._transport)
    assert p.ForkAction.TILT_UP in _fork_actions(node._transport)
