"""Yavas 180 derece donus, arka kamera hizalama ve serit takibi."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    lane_share = get_package_share_directory('lane_tracking')
    base_share = get_package_share_directory('marco_base')
    base = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(base_share, 'launch', 'base_driver.launch.py')),
        launch_arguments={
            'sahte': LaunchConfiguration('sahte'),
            'port': LaunchConfiguration('port'),
            'tf': 'false',
        }.items(),
    )
    sequence = Node(
        package='lane_tracking',
        executable='turn_then_rear_lane',
        name='turn_then_rear_lane_node',
        output='screen',
        parameters=[
            os.path.join(lane_share, 'config', 'turn_then_rear_lane.yaml'),
            {
                'camera_device': LaunchConfiguration('camera'),
                'odom_topic': LaunchConfiguration('odom_topic'),
                'turn_direction': ParameterValue(
                    LaunchConfiguration('turn_direction'), value_type=int),
                'steering_sign': ParameterValue(
                    LaunchConfiguration('steering_sign'), value_type=float),
            },
        ],
    )
    return LaunchDescription([
        DeclareLaunchArgument('sahte', default_value='false'),
        DeclareLaunchArgument('port', default_value='/dev/marco_stm32'),
        DeclareLaunchArgument('camera', default_value='/dev/video0'),
        DeclareLaunchArgument('odom_topic', default_value='/odom'),
        DeclareLaunchArgument('turn_direction', default_value='1'),
        DeclareLaunchArgument('steering_sign', default_value='-1.0'),
        base,
        sequence,
    ])
