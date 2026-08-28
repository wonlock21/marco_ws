"""Kamera serit takibi ile STM32 taban surucusunu birlikte baslatir.

Gercek donanim:
  ros2 launch lane_tracking lane_follow.launch.py
Sahte STM32 (UART olmadan zincir testi):
  ros2 launch lane_tracking lane_follow.launch.py sahte:=true
"""

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

    front_camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(lane_share, 'launch', 'front_camera.launch.py')),
        launch_arguments={
            'camera': LaunchConfiguration('camera'),
            'web_stream': LaunchConfiguration('web_stream'),
        }.items(),
    )

    base_driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(base_share, 'launch', 'base_driver.launch.py')),
        launch_arguments={
            'sahte': LaunchConfiguration('sahte'),
            'port': LaunchConfiguration('port'),
            'baud': LaunchConfiguration('baud'),
            'tf': 'false',
        }.items(),
    )

    imgprocess = Node(
        package='lane_tracking',
        executable='imgprocess',
        name='imgprocess_node',
        output='screen',
        parameters=[
            os.path.join(lane_share, 'config', 'lane_tracking.yaml'),
            {
                'camera_device': LaunchConfiguration('camera'),
                'camera_input': 'ros_topic',
                'camera_topic': '/camera/image_raw',
                'startup_mode': LaunchConfiguration('startup_mode'),
                # Donus dugumu bu komutlari normal suruste /cmd_vel'e aktarir.
                'output_topic': '/cmd_vel_lane',
                'show_debug_window': ParameterValue(
                    LaunchConfiguration('gui'), value_type=bool),
            },
        ],
    )

    turnaround = Node(
        package='lane_tracking',
        executable='turnaround',
        name='turnaround_node',
        output='screen',
        parameters=[
            os.path.join(lane_share, 'config', 'lane_tracking.yaml'),
            {
                'odom_topic': LaunchConfiguration('odom_topic'),
                'turn_direction': ParameterValue(
                    LaunchConfiguration('turn_direction'), value_type=int),
            },
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument('sahte', default_value='false'),
        DeclareLaunchArgument('port', default_value='/dev/marco_stm32'),
        DeclareLaunchArgument('baud', default_value='115200'),
        DeclareLaunchArgument(
            'camera', default_value='/dev/marco_front_camera'),
        DeclareLaunchArgument('web_stream', default_value='true'),
        DeclareLaunchArgument('startup_mode', default_value='LANE_TRACKING'),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('odom_topic', default_value='/odom'),
        DeclareLaunchArgument('turn_direction', default_value='1'),
        front_camera,
        base_driver,
        imgprocess,
        turnaround,
    ])
