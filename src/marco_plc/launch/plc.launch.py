"""Launch the fail-closed production PLC bridge."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    """Create the production bridge with a replaceable configuration file."""
    default_config = os.path.join(
        get_package_share_directory('marco_plc'), 'config', 'plc.yaml')
    return LaunchDescription([
        DeclareLaunchArgument('config_file', default_value=default_config),
        Node(
            package='marco_plc',
            executable='plc_bridge_node',
            name='real_plc_bridge',
            output='screen',
            parameters=[LaunchConfiguration('config_file')],
        ),
    ])
