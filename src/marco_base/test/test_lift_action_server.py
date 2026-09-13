"""Fail-closed behavior tests for the production STM32 lift action."""

import time
from types import SimpleNamespace

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
        self.writes.append(data)

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


def _goal(timeout=0.03):
    return SimpleNamespace(
        command=LiftLoad.Goal.COMMAND_PICKUP,
        station_id="A1",
        timeout=timeout,
    )


def _status(flags=p.StatusFlag(0)):
    return p.StatusFrame(0, flags, 12600, 0, 0, 30, 0)


def _fork_actions(transport):
    actions = []
    for raw in transport.writes:
        frames = list(p.FrameParser().feed(raw))
        for msg_id, payload in frames:
            if msg_id is p.MsgId.CMD_FORK:
                actions.append(p.decode_fork(payload)[0])
    return actions


def _healthy(node, flags=p.StatusFlag(0)):
    now = time.monotonic()
    node._status = _status(flags)
    node._last_valid_frame_wall = now
    node._last_status_wall = now


def _node():
    node = BaseDriver(parameter_overrides=[
        Parameter("use_fake_hardware", value=True),
        Parameter("wheel_measurement_log_enabled", value=False),
        Parameter("lift_action_server_enabled", value=True),
    ])
    node._transport = RecordingTransport()
    return node


def test_communication_loss_and_estop_reject_new_goal():
    rclpy.init()
    node = _node()
    try:
        assert node._lift_goal_callback(_goal()) == GoalResponse.REJECT
        _healthy(node, p.StatusFlag.ESTOP_ACTIVE)
        assert node._lift_goal_callback(_goal()) == GoalResponse.REJECT
    finally:
        node.destroy_node()
        rclpy.shutdown()


def test_duplicate_goal_is_rejected():
    rclpy.init()
    node = _node()
    try:
        _healthy(node)
        assert node._lift_goal_callback(_goal()) == GoalResponse.ACCEPT
        assert node._lift_goal_callback(_goal()) == GoalResponse.REJECT
    finally:
        node._lift_goal_active = False
        node.destroy_node()
        rclpy.shutdown()


def test_cancel_and_timeout_send_stop_without_success():
    rclpy.init()
    node = _node()
    try:
        _healthy(node)
        canceled = FakeGoalHandle(_goal())
        canceled.on_feedback = lambda: setattr(
            canceled, "is_cancel_requested", True
        )
        cancel_result = node._execute_lift(canceled)
        assert canceled.terminal == "canceled"
        assert not cancel_result.success
        cancel_actions = _fork_actions(node._transport)
        assert p.ForkAction.UP in cancel_actions
        assert cancel_actions[-1] is p.ForkAction.STOP

        node._transport.writes.clear()
        _healthy(node)
        timed_out = FakeGoalHandle(_goal())
        timeout_result = node._execute_lift(timed_out)
        assert timed_out.terminal == "aborted"
        assert timeout_result.result_code == LiftLoad.Result.RESULT_TIMEOUT
        actions = _fork_actions(node._transport)
        assert p.ForkAction.UP in actions
        assert actions[-1] is p.ForkAction.STOP
    finally:
        node.destroy_node()
        rclpy.shutdown()


def test_estop_during_motion_aborts_and_sends_stop():
    rclpy.init()
    node = _node()
    try:
        _healthy(node)

        def activate_estop():
            _healthy(node, p.StatusFlag.ESTOP_ACTIVE)

        handle = FakeGoalHandle(_goal(), on_feedback=activate_estop)
        result = node._execute_lift(handle)

        assert handle.terminal == "aborted"
        assert not result.success
        assert "e-stop" in result.message
        actions = _fork_actions(node._transport)
        assert p.ForkAction.UP in actions
        assert actions[-1] is p.ForkAction.STOP
    finally:
        node.destroy_node()
        rclpy.shutdown()


def test_real_limit_feedback_is_required_for_success():
    rclpy.init()
    node = _node()
    try:
        _healthy(node, p.StatusFlag.LIMIT_SWITCH_UP)
        handle = FakeGoalHandle(_goal())
        result = node._execute_lift(handle)
        assert handle.terminal == "succeeded"
        assert result.success
        assert result.result_code == LiftLoad.Result.RESULT_OK
        assert _fork_actions(node._transport)[-1] is p.ForkAction.STOP
    finally:
        node.destroy_node()
        rclpy.shutdown()
