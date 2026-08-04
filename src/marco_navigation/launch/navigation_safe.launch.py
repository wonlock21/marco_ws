"""AMCL + temel Nav2 + güvenli hız zinciri.

Zincir: Nav2 (cmd_vel_raw) -> Collision Monitor (cmd_vel_safe)
         -> twist_mux -> /cmd_vel -> STM32.

Bu launch dosyası temel pose navigasyonu içindir; rota grafiği için
``route_safe.launch.py`` kullanılmalıdır.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import SetRemap


def generate_launch_description() -> LaunchDescription:
    nav_share = get_package_share_directory("marco_navigation")
    safety_share = get_package_share_directory("marco_safety")

    nav2_safe = GroupAction(actions=[
        # navigation.launch içindeki Nav2 cmd_vel çıkışını güvenlik katmanına ver.
        SetRemap(src="cmd_vel", dst="cmd_vel_raw"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav_share, "launch", "navigation.launch.py")
            ),
            launch_arguments={
                "sahte": LaunchConfiguration("sahte"),
                "lidar": LaunchConfiguration("lidar"),
                "imu": LaunchConfiguration("imu"),
                "harita": LaunchConfiguration("harita"),
                "baslangic": LaunchConfiguration("baslangic"),
                "x": LaunchConfiguration("x"),
                "y": LaunchConfiguration("y"),
                "yaw": LaunchConfiguration("yaw"),
                "rviz": LaunchConfiguration("rviz"),
            }.items(),
        ),
    ])

    safety = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(safety_share, "launch", "safety.launch.py")
        ),
        launch_arguments={
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "scan_topic": LaunchConfiguration("scan_topic"),
        }.items(),
    )

    args = [
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument("sahte", default_value="true"),
        DeclareLaunchArgument("lidar", default_value="true"),
        DeclareLaunchArgument("imu", default_value="false"),
        DeclareLaunchArgument("harita", default_value="oda_test"),
        DeclareLaunchArgument("baslangic", default_value="true"),
        DeclareLaunchArgument("x", default_value="0.0"),
        DeclareLaunchArgument("y", default_value="0.0"),
        DeclareLaunchArgument("yaw", default_value="0.0"),
        DeclareLaunchArgument("rviz", default_value="false"),
        DeclareLaunchArgument("scan_topic", default_value="/scan"),
        LogInfo(msg="navigation_safe: Nav2 -> collision_monitor -> twist_mux -> /cmd_vel"),
        nav2_safe,
        safety,
    ]
    return LaunchDescription(args)
