"""Tek A veya B serit segmenti: kamera takibi + odometri kontrollu donus."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    lane_share = get_package_share_directory("lane_tracking")
    config = os.path.join(lane_share, "config", "lane_tracking.yaml")
    return LaunchDescription([
        DeclareLaunchArgument("camera", default_value="/dev/video0"),
        DeclareLaunchArgument("odom_topic", default_value="/odometry/filtered"),
        DeclareLaunchArgument("turn_direction", default_value="1"),
        Node(
            package="lane_tracking",
            executable="imgprocess",
            name="imgprocess_node",
            output="screen",
            parameters=[config, {
                "camera_device": LaunchConfiguration("camera"),
                "startup_mode": "LANE_TRACKING",
                "output_topic": "/cmd_vel_lane",
                "show_debug_window": False,
            }],
        ),
        Node(
            package="lane_tracking",
            executable="turnaround",
            name="turnaround_node",
            output="screen",
            parameters=[config, {
                "lane_command_topic": "/cmd_vel_lane",
                "output_topic": "/cmd_vel_raw",
                "odom_topic": LaunchConfiguration("odom_topic"),
                "turn_direction": ParameterValue(
                    LaunchConfiguration("turn_direction"), value_type=int
                ),
            }],
        ),
        LogInfo(msg="Demo serit komutu: /cmd_vel_raw -> safety -> /cmd_vel"),
    ])
