"""Focused policy tests for the Phase-8 safety supervisor."""

import importlib.util
import json
import time
from pathlib import Path

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


def make_supervisor():
    """Create a supervisor isolated from physical STM32 communication."""
    node = SafetySupervisor(parameter_overrides=[
        Parameter("require_base_communication", value=False),
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
