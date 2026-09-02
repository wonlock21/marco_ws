"""Saklanan YDLIDAR T-mini Pro surucu ve self-filter launch'i."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import LifecycleNode, Node


def generate_launch_description():
    localization_share = get_package_share_directory('marco_localization')
    params_file = os.path.join(
        localization_share,
        'config',
        'lidar_tmini_pro.yaml',
    )

    driver_node = LifecycleNode(
        package='ydlidar_ros2_driver',
        executable='ydlidar_ros2_driver_node',
        name='ydlidar_ros2_driver_node',
        output='screen',
        emulate_tty=True,
        parameters=[params_file],
        namespace='/',
        remappings=[('scan', '/scan_raw')],
    )

    filter_node = Node(
        package='lidar_filter',
        executable='self_scan_filter',
        name='self_scan_filter',
        output='screen',
    )

    return LaunchDescription([driver_node, filter_node])
