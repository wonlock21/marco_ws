"""Lift takiliyken yalniz sakin on-kamera serit takibini baslatir.

Bu launch turnaround ve arka-kamera siralama dugumlerini bilerek baslatmaz.
Serit sonu algilanirsa imgprocess dur komutu verir ve hareketsiz kalir.
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
            os.path.join(lane_share, 'config', 'lane_follow_lift_safe.yaml'),
            {
                'camera_device': LaunchConfiguration('camera'),
                'camera_input': 'ros_topic',
                'camera_topic': '/camera/image_raw',
                'startup_mode': 'LANE_TRACKING',
                'output_topic': '/cmd_vel',
                'show_debug_window': ParameterValue(
                    LaunchConfiguration('gui'), value_type=bool),
            },
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument('sahte', default_value='false'),
        DeclareLaunchArgument('port', default_value='/dev/marco_stm32'),
        DeclareLaunchArgument(
            'camera', default_value='/dev/marco_front_camera'),
        DeclareLaunchArgument('web_stream', default_value='true'),
        DeclareLaunchArgument('gui', default_value='false'),
        front_camera,
        base_driver,
        imgprocess,
    ])
