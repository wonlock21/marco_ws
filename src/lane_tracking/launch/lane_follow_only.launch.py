"""Yalniz liftsiz/orijinal on-kamera serit takibini baslatir.

Turnaround ve arka-kamera dugumleri yoktur. Serit kaybinda arac durur, serit
yeniden gorundugunde takip devam eder; serit-sonu durumuna gecilmez.
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

    camera_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                lane_share, 'launch',
                'front_camera_compressed.launch.py')),
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
                'camera_input': LaunchConfiguration('camera_input'),
                'camera_topic': LaunchConfiguration('camera_topic'),
                'camera_compressed_topic': LaunchConfiguration(
                    'camera_compressed_topic'),
                'startup_mode': 'LANE_TRACKING',
                'output_topic': '/cmd_vel',
                'show_debug_window': ParameterValue(
                    LaunchConfiguration('gui'), value_type=bool),
                'lane_end_detection_enabled': False,
            },
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument('sahte', default_value='false'),
        DeclareLaunchArgument('port', default_value='/dev/marco_stm32'),
        DeclareLaunchArgument(
            'camera', default_value='/dev/marco_front_camera'),
        DeclareLaunchArgument(
            'camera_input', default_value='ros_compressed'),
        DeclareLaunchArgument(
            'camera_topic', default_value='/camera/image_raw'),
        DeclareLaunchArgument(
            'camera_compressed_topic',
            default_value='/camera/image_raw/compressed'),
        DeclareLaunchArgument('web_stream', default_value='true'),
        DeclareLaunchArgument('gui', default_value='false'),
        camera_node,
        base_driver,
        imgprocess,
    ])
