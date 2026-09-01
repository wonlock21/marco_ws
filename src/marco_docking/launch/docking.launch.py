r"""
Hassas yanasma (Faz 9): dock_server + istege bagli perception mock.

    ros2 launch marco_docking docking.launch.py mock:=false

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
    lane_share = get_package_share_directory("lane_tracking")
    params = os.path.join(dock_share, "config", "docking.yaml")

    mock = LaunchConfiguration("mock")
    station = LaunchConfiguration("station_id")
    scenario = LaunchConfiguration("scenario")
    lane_tracking = LaunchConfiguration("lane_tracking")

    dock = Node(
        package="marco_docking",
        executable="dock_server",
        name="dock_server",
        output="screen",
        parameters=[params],
    )

    lane = Node(
        package="lane_tracking",
        executable="imgprocess",
        name="imgprocess_node",
        output="screen",
        condition=IfCondition(lane_tracking),
        parameters=[
            os.path.join(lane_share, "config", "lane_tracking.yaml"),
            {
                "camera_input": "ros_topic",
                "camera_topic": "/camera/image_raw",
                "startup_mode": "IDLE",
                "output_topic": "/cmd_vel_lane",
                "show_debug_window": False,
                "lane_end_detection_enabled": False,
            },
        ],
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
                default_value="false",
                description="true: sahte /lane/offset + /qr/detection",
            ),
            DeclareLaunchArgument(
                "lane_tracking",
                default_value="true",
                description="gercek arka kamera serit cikisini IDLE baslat",
            ),
            DeclareLaunchArgument("station_id", default_value="istasyon_A"),
            DeclareLaunchArgument(
                "scenario",
                default_value="success",
                description="success | qr_mismatch | lane_lost",
            ),
            LogInfo(msg=["docking launch mock=", mock, " station=", station]),
            dock,
            lane,
            perception_mock,
        ]
    )
