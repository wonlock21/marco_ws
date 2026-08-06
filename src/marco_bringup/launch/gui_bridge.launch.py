"""Local-network rosbridge endpoint shared by the desktop and mobile GUIs."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        DeclareLaunchArgument('address', default_value='0.0.0.0'),
        DeclareLaunchArgument('port', default_value='9090'),
        Node(
            package='rosbridge_server',
            executable='rosbridge_websocket',
            name='gui_rosbridge_websocket',
            output='screen',
            parameters=[{
                'address': LaunchConfiguration('address'),
                'port': ParameterValue(LaunchConfiguration('port'), value_type=int),
                'use_compression': False,
                'call_services_in_new_thread': True,
                'send_action_goals_in_new_thread': True,
            }],
        ),
    ])
