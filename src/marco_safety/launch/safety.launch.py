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
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    share = get_package_share_directory("marco_safety")
    cm_params = os.path.join(share, "config", "collision_monitor.yaml")
    mux_params = os.path.join(share, "config", "twist_mux.yaml")

    use_sim_time = LaunchConfiguration("use_sim_time")
    obstacle_detection = ParameterValue(
        LaunchConfiguration("obstacle_detection"), value_type=bool
    )

    collision_monitor = Node(
        package="nav2_collision_monitor",
        executable="collision_monitor",
        name="collision_monitor",
        output="screen",
        parameters=[cm_params, {
            "use_sim_time": use_sim_time,
            "FrontStop.enabled": obstacle_detection,
            "RearStop.enabled": obstacle_detection,
            "FrontSlow.enabled": obstacle_detection,
            "RearSlow.enabled": obstacle_detection,
        }],
        remappings=[("tf", "/tf"), ("tf_static", "/tf_static"),
                    ("scan", LaunchConfiguration("scan_topic"))],
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

    supervisor = Node(
        package="marco_safety",
        executable="safety_supervisor.py",
        name="safety_supervisor",
        output="screen",
        parameters=[{
            "use_sim_time": use_sim_time,
            "base_frame": LaunchConfiguration("base_frame"),
            "scan_timeout_s": ParameterValue(
                LaunchConfiguration("scan_timeout_s"), value_type=float),
            "tf_timeout_s": ParameterValue(
                LaunchConfiguration("tf_timeout_s"), value_type=float),
            "input_timeout_s": ParameterValue(
                LaunchConfiguration("input_timeout_s"), value_type=float),
            "base_communication_timeout_s": ParameterValue(
                LaunchConfiguration("base_communication_timeout_s"),
                value_type=float),
            "require_base_communication": ParameterValue(
                LaunchConfiguration("require_base_communication"),
                value_type=bool),
            "obstacle_wait_timeout_s": ParameterValue(
                LaunchConfiguration("obstacle_wait_timeout_s"), value_type=float),
            "obstacle_detection_enabled": obstacle_detection,
        }],
        remappings=[("scan", LaunchConfiguration("scan_topic"))],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("scan_topic", default_value="/scan"),
            DeclareLaunchArgument("base_frame", default_value="base_footprint"),
            DeclareLaunchArgument("scan_timeout_s", default_value="0.5"),
            DeclareLaunchArgument("tf_timeout_s", default_value="0.5"),
            DeclareLaunchArgument("input_timeout_s", default_value="0.5"),
            DeclareLaunchArgument(
                "base_communication_timeout_s", default_value="0.75"),
            DeclareLaunchArgument(
                "require_base_communication", default_value="true"),
            DeclareLaunchArgument(
                "obstacle_wait_timeout_s",
                default_value="0.0",
                description=(
                    "0: engel kalkana kadar guvenli bekle; pozitif deger yalniz "
                    "acikca istenen test profillerinde navigasyonu iptal eder"
                ),
            ),
            DeclareLaunchArgument("obstacle_detection", default_value="true"),
            LogInfo(msg=f"collision_monitor: {cm_params}"),
            LogInfo(msg=f"twist_mux: {mux_params}"),
            collision_monitor,
            lifecycle,
            twist_mux,
            supervisor,
        ]
    )
