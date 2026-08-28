"""
Sahte serit/QR (goruntu ekibi yerine).

ros2 launch marco_perception mock_perception.launch.py
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument("scenario", default_value="success"),
            DeclareLaunchArgument("station_id", default_value="istasyon_A"),
            Node(
                package="marco_perception",
                executable="mock_lane_qr",
                name="mock_lane_qr",
                output="screen",
                parameters=[
                    {
                        "scenario": LaunchConfiguration("scenario"),
                        "station_id": LaunchConfiguration("station_id"),
                        "rate_hz": 20.0,
                    }
                ],
            ),
        ]
    )
