"""Unit tests for the F7C timed rear-lane adapter."""

import math

from geometry_msgs.msg import Twist
import pytest

from marco_docking.dock_server import reverse_lane_command


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
