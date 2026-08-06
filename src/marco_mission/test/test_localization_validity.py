"""Unit tests for mission localization health validation."""

import math

from marco_mission.localization_validity import evaluate_localization


def _health(**overrides):
    values = {
        'has_pose': True,
        'pose_finite': True,
        'position_covariance': 0.2,
        'max_position_covariance': 1.0,
        'map_odom_tf_age': 0.1,
        'odom_base_tf_age': 0.1,
        'tf_timeout': 2.0,
        'scan_age': 0.1,
        'scan_timeout': 2.0,
        'odom_age': 0.1,
        'odom_timeout': 2.0,
    }
    values.update(overrides)
    return evaluate_localization(**values)


def test_stationary_robot_remains_valid_without_new_amcl_pose():
    """AMCL callback age is deliberately absent from the health inputs."""
    assert _health().valid


def test_missing_tf_is_invalid_and_reports_chain_member():
    health = _health(map_odom_tf_age=None)
    assert not health.valid
    assert 'map->odom TF bulunamadi' in health.reason


def test_stale_scan_is_invalid():
    health = _health(scan_age=2.1)
    assert not health.valid
    assert '/scan stale' in health.reason


def test_stale_odom_is_invalid():
    health = _health(odom_age=2.1)
    assert not health.valid
    assert 'odometri stale' in health.reason


def test_nan_covariance_is_invalid():
    health = _health(position_covariance=math.nan, pose_finite=False)
    assert not health.valid
    assert 'finite degil' in health.reason


def test_pose_not_received_is_invalid():
    health = _health(has_pose=False, pose_finite=False)
    assert not health.valid
    assert 'henuz alinmadi' in health.reason
