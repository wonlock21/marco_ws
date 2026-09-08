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


def test_reverse_lane_command_reverses_and_bounds_motion():
    lane = Twist()
    lane.linear.x = 0.08
    lane.angular.z = 0.50

    command = reverse_lane_command(lane, -1.0, 0.05, 0.40)

    assert command.linear.x == pytest.approx(-0.05)
    assert command.angular.z == pytest.approx(-0.40)


def test_reverse_lane_command_rejects_non_finite_input():
    lane = Twist()
    lane.linear.x = math.nan

    with pytest.raises(ValueError, match="non-finite"):
        reverse_lane_command(lane, -1.0, 0.05, 0.40)


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
    timeout, publish_fresh_end, zero_without_end=False
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
        'odom_timeout_s': 1.0,
        'stop_timeout_s': 0.05,
        'stop_settle_s': 0.0,
        'stop_linear_tolerance': 0.01,
        'stop_angular_tolerance': 0.03,
        'reverse_angular_sign': -1.0,
        'max_linear_vel': 0.05,
        'max_angular_vel': 0.40,
    }
    server._estop = False
    server._obstacle = False
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
            if publish_fresh_end:
                server._on_lane_end(Bool(data=True))

    server._task_pub = _Publisher(task_command)
    server._pub = _Publisher(dock_command)
    return server


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
