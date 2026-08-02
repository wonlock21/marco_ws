"""AMCL + Nav2 + nav2_route + guvenlik (Faz 7+8).

Nav2 smoother cikisi /cmd_vel yerine /cmd_vel_raw'a yonlenir;
collision_monitor + twist_mux /cmd_vel uretir.

  ros2 launch marco_navigation route_safe.launch.py \\
      sahte:=true lidar:=true harita:=nav_test baslangic:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    LogInfo,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import SetRemap


def generate_launch_description() -> LaunchDescription:
    nav_share = get_package_share_directory("marco_navigation")
    safety_share = get_package_share_directory("marco_safety")

    # Nav2 velocity_smoother'in yayinladigi cmd_vel → cmd_vel_raw
    # (navigation_launch icindeki hedef remap uzerine ek katman).
    route_with_raw = GroupAction(
        actions=[
            SetRemap(src="cmd_vel", dst="cmd_vel_raw"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(nav_share, "launch", "route.launch.py")
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
                    "graf": LaunchConfiguration("graf"),
                }.items(),
            ),
        ]
    )

    safety = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(safety_share, "launch", "safety.launch.py")
        ),
        launch_arguments={"use_sim_time": "false"}.items(),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("sahte", default_value="true"),
            DeclareLaunchArgument("lidar", default_value="true"),
            DeclareLaunchArgument("imu", default_value="false"),
            DeclareLaunchArgument("harita", default_value="nav_test"),
            DeclareLaunchArgument("baslangic", default_value="true"),
            DeclareLaunchArgument("x", default_value="0.0"),
            DeclareLaunchArgument("y", default_value="0.0"),
            DeclareLaunchArgument("yaw", default_value="0.0"),
            DeclareLaunchArgument("graf", default_value=""),
            LogInfo(
                msg="route_safe: cmd_vel_raw → collision_monitor → twist_mux → cmd_vel"
            ),
            route_with_raw,
            safety,
        ]
    )
