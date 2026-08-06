"""Pure localization health checks shared by mission admission and status."""

from dataclasses import dataclass
import math
from typing import Optional


@dataclass(frozen=True)
class LocalizationHealth:
    """Result of a localization health evaluation."""

    valid: bool
    reason: str


def evaluate_localization(*, has_pose: bool, pose_finite: bool,
                          position_covariance: float,
                          max_position_covariance: float,
                          map_odom_tf_age: Optional[float],
                          odom_base_tf_age: Optional[float],
                          tf_timeout: float,
                          scan_age: Optional[float], scan_timeout: float,
                          odom_age: Optional[float],
                          odom_timeout: float) -> LocalizationHealth:
    """Evaluate localization inputs without using the AMCL callback age."""
    if not has_pose:
        return LocalizationHealth(False, 'AMCL pozu henuz alinmadi')
    if not pose_finite or not math.isfinite(position_covariance):
        return LocalizationHealth(
            False, 'AMCL poz veya kovaryans degeri finite degil')
    if position_covariance > max_position_covariance:
        return LocalizationHealth(
            False,
            'AMCL konum kovaryansi esigi asti '
            f'({position_covariance:.3f} > {max_position_covariance:.3f})')

    for name, age in (('map->odom', map_odom_tf_age),
                      ('odom->base_footprint', odom_base_tf_age)):
        if age is None:
            return LocalizationHealth(False, f'{name} TF bulunamadi')
        if age > tf_timeout:
            return LocalizationHealth(
                False, f'{name} TF stale ({age:.2f}s > {tf_timeout:.2f}s)')

    if scan_age is None:
        return LocalizationHealth(False, '/scan henuz alinmadi')
    if scan_age > scan_timeout:
        return LocalizationHealth(
            False, f'/scan stale ({scan_age:.2f}s > {scan_timeout:.2f}s)')
    if odom_age is None:
        return LocalizationHealth(
            False, '/odom veya /odometry/filtered henuz alinmadi')
    if odom_age > odom_timeout:
        return LocalizationHealth(
            False, 'odometri stale '
            f'({odom_age:.2f}s > {odom_timeout:.2f}s)')
    return LocalizationHealth(True, 'lokalizasyon gecerli')
