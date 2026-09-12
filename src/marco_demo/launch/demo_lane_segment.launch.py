"""Tek A veya B serit segmenti icin kamera tabanli takip."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    lane_share = get_package_share_directory("lane_tracking")
    config = os.path.join(lane_share, "config", "lane_tracking.yaml")
    front_camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(lane_share, "launch", "front_camera.launch.py")
        ),
        launch_arguments={
            "camera": LaunchConfiguration("camera"),
            "web_stream": LaunchConfiguration("web_stream"),
        }.items(),
    )
    return LaunchDescription([
        DeclareLaunchArgument(
            "camera", default_value="/dev/marco_front_camera"
        ),
        DeclareLaunchArgument("web_stream", default_value="true"),
        front_camera,
        Node(
            package="lane_tracking",
            executable="imgprocess",
            name="imgprocess_node",
            output="screen",
            parameters=[config, {
                "camera_device": LaunchConfiguration("camera"),
                "camera_input": "ros_topic",
                "camera_topic": "/camera/image_raw",
                "startup_mode": "LANE_TRACKING",
                "output_topic": "/cmd_vel_raw",
                "show_debug_window": False,
            }],
        ),
        LogInfo(msg="Demo serit komutu: /cmd_vel_raw -> safety -> /cmd_vel"),
    ])
