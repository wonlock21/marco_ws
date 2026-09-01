"""Launch the semantic field route editor."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        DeclareLaunchArgument(
            "data_root",
            default_value="~/marco_data/fields",
            description="Mapped field package root",
        ),
        DeclareLaunchArgument(
            "competition_profile",
            default_value="true",
            description="Require the complete WAIT/A/B/q5 competition graph",
        ),
        Node(
            package="marco_route",
            executable="route_editor",
            name="route_editor",
            output="screen",
            parameters=[{
                "data_root": LaunchConfiguration("data_root"),
                "competition_profile": LaunchConfiguration("competition_profile"),
            }],
        ),
    ])
