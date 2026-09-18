"""Focused policy tests for the Phase-8 safety supervisor."""

import importlib.util
import json
import time
from pathlib import Path

import pytest
import rclpy
from geometry_msgs.msg import TransformStamped, Twist
from rclpy.parameter import Parameter
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool
from std_srvs.srv import Trigger


SCRIPT = Path(__file__).parents[1] / "scripts" / "safety_supervisor.py"
SPEC = importlib.util.spec_from_file_location("safety_supervisor", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SafetySupervisor = MODULE.SafetySupervisor


class Recorder:
    """Minimal publisher replacement retaining published ROS messages."""

    def __init__(self):
        self.messages = []

    def publish(self, message):
        self.messages.append(message)


def make_supervisor(
    *,
    require_base_communication=False,
    recovery_stable=0.5,
):
    """Create a supervisor isolated from physical STM32 communication."""
    node = SafetySupervisor(parameter_overrides=[
        Parameter(
            "require_base_communication",
            value=require_base_communication,
        ),
        Parameter(
            "base_communication_recovery_stable_s",
            value=recovery_stable,
        ),
        Parameter("scan_timeout_s", value=1.0),
        Parameter("tf_timeout_s", value=1.0),
        Parameter("input_timeout_s", value=1.0),
        Parameter("obstacle_wait_timeout_s", value=0.0),
    ])
    transform = TransformStamped()
    transform.header.frame_id = "base_footprint"
    transform.child_frame_id = "laser"
    transform.transform.rotation.w = 1.0
    node._tf.set_transform_static(transform, "phase8_test")
    node._guard_pub = Recorder()
    node._obstacle_pub = Recorder()
    node._state_pub = Recorder()
    node._abort_pub = Recorder()
    return node


def scan(*ranges):
    """Build a front-facing scan with deterministic valid ranges."""
    message = LaserScan()
    message.header.frame_id = "laser"
    message.angle_min = -0.05
    message.angle_increment = 0.05
    message.range_min = 0.05
    message.range_max = 10.0
    message.ranges = list(ranges)
    return message


def moving_twist(speed=0.2):
    """Return one finite forward command."""
    message = Twist()
    message.linear.x = speed
    return message


def test_obstacle_guards_all_sources_without_automatic_timeout():
    """A permanent obstacle stays a zero guard and never aborts by time."""
    rclpy.init()
    node = make_supervisor()
    try:
        node._on_input("dock", moving_twist(-0.2))
        node._on_scan(scan(0.50, 0.52, 0.54))
        node._tick()

        assert "obstacle" in node._current_reasons
        assert "obstacle_wait_timeout" not in node._current_reasons
        assert node._guard_pub.messages
        assert node._guard_pub.messages[-1] == Twist()

        node._stop_since = time.monotonic() - 121.0
        node._tick()
        state = json.loads(node._state_pub.messages[-1].data)
        assert state["waiting_for_obstacle_clear"]
        assert state["obstacle_wait_s"] >= 120.0
        assert "obstacle_wait_timeout" not in state["reason"]
        assert not any(message.data for message in node._abort_pub.messages)

        node._on_scan(scan(5.0, 5.0, 5.0))
        node._tick()
        assert "obstacle" not in node._current_reasons
        assert node._obstacle_pub.messages[-1] == Bool(data=False)
    finally:
        node.destroy_node()
        rclpy.shutdown()


def test_estop_release_requires_explicit_zero_command_reset():
    """Releasing E-stop cannot resume a still-active command by itself."""
    rclpy.init()
    node = make_supervisor()
    cancel_calls = []
    node._cancel_navigation = lambda: cancel_calls.append(True)
    try:
        node._on_scan(scan(5.0, 5.0, 5.0))
        node._on_input("nav", moving_twist())
        node._on_estop(Bool(data=True))
        node._tick()
        assert cancel_calls == [True]
        assert node._operator_reset_required
        assert node._abort_pub.messages[-1] == Bool(data=True)

        node._on_estop(Bool(data=False))
        rejected = node._on_reset(Trigger.Request(), Trigger.Response())
        assert not rejected.success
        assert "nav" in rejected.message

        node._on_input("nav", Twist())
        node._tick()
        accepted = node._on_reset(Trigger.Request(), Trigger.Response())
        assert accepted.success
        assert not node._operator_reset_required
        assert node._abort_pub.messages[-1] == Bool(data=False)
    finally:
        node.destroy_node()
        rclpy.shutdown()


def test_communication_recovery_holds_zero_until_stable(monkeypatch):
    """Loss and the complete stable window override an active Nav2 input."""
    now = [100.0]
    monkeypatch.setattr(MODULE.time, "monotonic", lambda: now[0])
    rclpy.init()
    node = make_supervisor(require_base_communication=True)
    try:
        node._on_scan(scan(5.0, 5.0, 5.0))
        node._on_input("nav", moving_twist())

        node._on_base_communication(Bool(data=False))
        assert node._guard_pub.messages[-1] == Twist()
        node._tick()
        assert "base_communication_lost" in node._current_reasons

        now[0] = 100.1
        node._on_base_communication(Bool(data=True))
        guard_count = len(node._guard_pub.messages)

        now[0] = 100.59
        node._on_scan(scan(5.0, 5.0, 5.0))
        node._on_input("nav", moving_twist())
        node._tick()
        assert "base_communication_recovery_hold" in node._current_reasons
        assert node._guard_pub.messages[-1] == Twist()
        assert len(node._guard_pub.messages) == guard_count + 1

        guard_count = len(node._guard_pub.messages)
        now[0] = 100.6
        node._on_scan(scan(5.0, 5.0, 5.0))
        node._on_input("nav", moving_twist())
        node._tick()
        state = json.loads(node._state_pub.messages[-1].data)
        assert "base_communication_recovery_hold" not in node._current_reasons
        assert not state["guard_zero"]
        assert state["selected_input"] == "nav"
        assert state["input_fresh"]
        assert not state["base_communication_recovery_active"]
        assert len(node._guard_pub.messages) == guard_count
    finally:
        node.destroy_node()
        rclpy.shutdown()


def test_communication_flap_restarts_stable_window(monkeypatch):
    """A short true pulse never releases zero or preserves healthy time."""
    now = [200.0]
    monkeypatch.setattr(MODULE.time, "monotonic", lambda: now[0])
    rclpy.init()
    node = make_supervisor(require_base_communication=True)
    try:
        node._on_base_communication(Bool(data=False))
        now[0] = 200.1
        node._on_base_communication(Bool(data=True))
        assert node._base_communication_healthy_since == 200.1

        now[0] = 200.3
        node._on_base_communication(Bool(data=False))
        assert node._base_communication_healthy_since is None

        now[0] = 200.4
        node._on_base_communication(Bool(data=True))
        holding, healthy_s = node._communication_recovery_holding(
            200.89, communication_fresh=True)
        assert holding
        assert healthy_s == pytest.approx(0.49)

        holding, healthy_s = node._communication_recovery_holding(
            200.9, communication_fresh=True)
        assert not holding
        assert healthy_s == pytest.approx(0.5)
    finally:
        node.destroy_node()
        rclpy.shutdown()
