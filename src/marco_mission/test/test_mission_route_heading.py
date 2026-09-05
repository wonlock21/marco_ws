"""Production route-heading and profile-aware maneuver health tests."""

import math
import time
from types import SimpleNamespace

import pytest
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav_msgs.msg import Path

from marco_mission.mission_manager import MissionAbort
from marco_mission.mission_manager import MissionActionFailure
from marco_mission.mission_manager import MissionManager
from marco_mission.mission_manager import _last_path_segment_heading
from marco_mission.mission_manager import _terminal_abort_is_acceptable


def _path(*coordinates):
    path = Path()
    path.header.frame_id = 'map'
    for x, y in coordinates:
        pose = PoseStamped()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.orientation.w = 1.0
        path.poses.append(pose)
    return path


def _pose(x, y, yaw):
    pose = PoseWithCovarianceStamped()
    pose.pose.pose.position.x = x
    pose.pose.pose.position.y = y
    pose.pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.pose.orientation.w = math.cos(yaw / 2.0)
    return pose


class _NavigationProbe:
    _yaw_from_pose = staticmethod(MissionManager._yaw_from_pose)

    def __init__(self, path, follow_status=GoalStatus.STATUS_SUCCEEDED):
        self._path = path
        self._follow_status = follow_status
        self._compute_route = object()
        self._follow_path = object()
        self._nodes = {'q5': {'id': 5, 'yaw': -1.2}}
        self._current_node = 'D3'
        self._edge = ''
        self._pose = _pose(
            path.poses[-1].pose.position.x - 0.02,
            path.poses[-1].pose.position.y,
            _last_path_segment_heading(path),
        )
        self.follow_goal = None
        self.events = []

    def _await_route_constraints(self):
        return None

    def _set_state(self, _state, _target):
        return None

    def _action(self, client, goal, label):
        if client is self._compute_route:
            return SimpleNamespace(path=self._path)
        self.follow_goal = goal
        if self._follow_status != GoalStatus.STATUS_SUCCEEDED:
            raise MissionActionFailure(label, self._follow_status)
        return SimpleNamespace()

    def get_parameter(self, name):
        values = {
            'route_terminal_position_tolerance_m': 0.075,
            'route_terminal_yaw_tolerance_deg': 10.0,
        }
        return SimpleNamespace(value=values[name])

    def _localization_health(self):
        return SimpleNamespace(valid=True)

    def _event(self, event, **fields):
        self.events.append((event, fields))


def test_last_path_heading_skips_duplicate_terminal_pose():
    path = _path((0.0, 0.0), (1.0, 0.0), (1.0, 2.0), (1.0, 2.0))

    assert _last_path_segment_heading(path) == pytest.approx(math.pi / 2.0)


def test_production_navigation_uses_route_heading_not_saved_node_yaw():
    probe = _NavigationProbe(_path((0.0, 0.0), (1.0, 0.0), (1.0, 2.0)))

    MissionManager._navigate(probe, 'q5', loaded=True)

    orientation = probe.follow_goal.path.poses[-1].pose.orientation
    yaw = math.atan2(
        2.0 * orientation.w * orientation.z,
        1.0 - 2.0 * orientation.z * orientation.z,
    )
    assert yaw == pytest.approx(math.pi / 2.0)
    assert yaw != pytest.approx(probe._nodes['q5']['yaw'])


def test_small_terminal_yaw_abort_is_accepted_after_reaching_goal():
    probe = _NavigationProbe(
        _path((0.0, 0.0), (1.0, 0.0)),
        follow_status=GoalStatus.STATUS_ABORTED,
    )

    MissionManager._navigate(probe, 'q5', loaded=False)

    assert probe._current_node == 'q5'
    assert any(
        event == 'route_terminal_abort_accepted'
        for event, _fields in probe.events
    )


def test_terminal_abort_outside_position_tolerance_is_rejected():
    accepted, position_error, _yaw_error = _terminal_abort_is_acceptable(
        target_x=1.0,
        target_y=0.0,
        target_yaw=0.0,
        robot_x=0.90,
        robot_y=0.0,
        robot_yaw=0.0,
        position_tolerance=0.075,
        yaw_tolerance=math.radians(10.0),
    )

    assert not accepted
    assert position_error == pytest.approx(0.10)


def test_terminal_abort_is_not_accepted_with_invalid_localization():
    probe = _NavigationProbe(
        _path((0.0, 0.0), (1.0, 0.0)),
        follow_status=GoalStatus.STATUS_ABORTED,
    )
    probe._localization_health = lambda: SimpleNamespace(valid=False)

    with pytest.raises(MissionActionFailure):
        MissionManager._navigate(probe, 'q5', loaded=False)


def _health_probe(imu_enabled, imu_age=999.0, odom_age=0.0):
    manager = MissionManager.__new__(MissionManager)
    manager._imu_enabled = imu_enabled
    manager._imu_seen = time.monotonic() - imu_age
    manager._filtered_odom_seen = time.monotonic() - odom_age
    manager._odom_freshness = 1.0
    manager.get_parameter = lambda _name: SimpleNamespace(value=0.5)
    manager._localization_health = lambda: SimpleNamespace(valid=True)
    return manager


def test_imu_disabled_profile_does_not_require_imu_freshness():
    manager = _health_probe(imu_enabled=False)

    manager._check_action_health(require_turn_sensors=True)


def test_imu_enabled_profile_fails_safe_on_stale_imu():
    manager = _health_probe(imu_enabled=True)

    with pytest.raises(MissionAbort, match='IMU verisi bayat'):
        manager._check_action_health(require_turn_sensors=True)


def test_imu_disabled_profile_still_requires_filtered_odometry():
    manager = _health_probe(imu_enabled=False, odom_age=2.0)

    with pytest.raises(MissionAbort, match='filtreli odometri bayat'):
        manager._check_action_health(require_turn_sensors=True)
