"""GUI haritalamasi: mapping + guvenli manuel hiz zinciri."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description() -> LaunchDescription:
    localization_share = get_package_share_directory("marco_localization")
    safety_share = get_package_share_directory("marco_safety")

    mapping = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(localization_share, "launch", "mapping.launch.py")
        ),
        launch_arguments={
            "sahte": LaunchConfiguration("sahte"),
            "lidar": LaunchConfiguration("lidar"),
            "imu": LaunchConfiguration("imu"),
            "serial_port": LaunchConfiguration("serial_port"),
            "lidar_port": LaunchConfiguration("lidar_port"),
            "rviz": LaunchConfiguration("rviz"),
        }.items(),
    )
    safety = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(safety_share, "launch", "safety.launch.py")
        ),
        launch_arguments={
            "use_sim_time": "false",
            "obstacle_detection": LaunchConfiguration("obstacle_detection"),
            # Guvenlik de nihai filtrelenmis LiDAR sozlesmesini kullanir.
            "scan_topic": "/scan",
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument("sahte", default_value="false"),
        DeclareLaunchArgument("lidar", default_value="true"),
        DeclareLaunchArgument("imu", default_value="false"),
        DeclareLaunchArgument("obstacle_detection", default_value="true"),
        DeclareLaunchArgument("serial_port", default_value="/dev/marco_stm32"),
        DeclareLaunchArgument("lidar_port", default_value="/dev/marco_lidar"),
        DeclareLaunchArgument("rviz", default_value="false"),
        LogInfo(msg="Manuel surus: /cmd_vel_manual -> twist_mux -> /cmd_vel"),
        mapping,
        safety,
    ])
