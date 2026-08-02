"""Hassas yanasma (Faz 9): dock_server + istege bagli perception mock.

  ros2 launch marco_docking docking.launch.py mock:=true

  ros2 action send_goal /dock_to_station marco_msgs/action/DockToStation \\
    "{station_id: 'istasyon_A', position_tolerance: 0.075, yaw_tolerance: 0.087,
      approach_type: 0, timeout: 60.0}"
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    dock_share = get_package_share_directory("marco_docking")
    params = os.path.join(dock_share, "config", "docking.yaml")

    mock = LaunchConfiguration("mock")
    station = LaunchConfiguration("station_id")
    scenario = LaunchConfiguration("scenario")

    dock = Node(
        package="marco_docking",
        executable="dock_server",
        name="dock_server",
        output="screen",
        parameters=[params],
    )

    perception_mock = Node(
        package="marco_perception",
        executable="mock_lane_qr",
        name="mock_lane_qr",
        output="screen",
        condition=IfCondition(mock),
        parameters=[
            {
                "scenario": scenario,
                "station_id": station,
                "rate_hz": 20.0,
            }
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "mock",
                default_value="true",
                description="true: sahte /lane/offset + /qr/detection",
            ),
            DeclareLaunchArgument("station_id", default_value="istasyon_A"),
            DeclareLaunchArgument(
                "scenario",
                default_value="success",
                description="success | qr_mismatch | lane_lost",
            ),
            LogInfo(msg=["docking launch mock=", mock, " station=", station]),
            dock,
            perception_mock,
        ]
    )
