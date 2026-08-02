"""MarCO guvenlik katmani (Faz 8).

Zincir:
  /cmd_vel_raw  → collision_monitor → /cmd_vel_safe
  /cmd_vel_safe + /cmd_vel_manual + /cmd_vel_dock + kilitler
                → twist_mux → /cmd_vel

Nav2 smoother ciktisi /cmd_vel_raw olmali (route_safe.launch SetRemap).

Ornek (tek basina, robot ayaktayken):
  ros2 launch marco_safety safety.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    share = get_package_share_directory("marco_safety")
    cm_params = os.path.join(share, "config", "collision_monitor.yaml")
    mux_params = os.path.join(share, "config", "twist_mux.yaml")

    use_sim_time = LaunchConfiguration("use_sim_time")

    collision_monitor = Node(
        package="nav2_collision_monitor",
        executable="collision_monitor",
        name="collision_monitor",
        output="screen",
        parameters=[cm_params, {"use_sim_time": use_sim_time}],
        remappings=[("tf", "/tf"), ("tf_static", "/tf_static")],
    )

    lifecycle = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_safety",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "autostart": True,
                "node_names": ["collision_monitor"],
            }
        ],
    )

    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        name="twist_mux",
        output="screen",
        parameters=[mux_params, {"use_sim_time": use_sim_time}],
        remappings=[("cmd_vel_out", "/cmd_vel")],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            LogInfo(msg=f"collision_monitor: {cm_params}"),
            LogInfo(msg=f"twist_mux: {mux_params}"),
            collision_monitor,
            lifecycle,
            twist_mux,
        ]
    )
