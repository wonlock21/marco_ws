import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    localization_share = get_package_share_directory('marco_localization')

    params_file = os.path.join(
        localization_share,
        'config',
        'lidar_rplidar_a2m12.yaml'
    )

    driver_node = Node(
        package='rplidar_ros',
        executable='rplidar_node',
        name='rplidar_node',
        output='screen',
        parameters=[params_file],
        namespace='/',
        remappings=[
            ('scan', '/scan_raw'),
        ],
    )

    filter_node = Node(
        package='lidar_filter',
        executable='self_scan_filter',
        name='self_scan_filter',
        output='screen',
	parameters=[{
        'blocked_regions_deg': [-70.0, 70.0],
    }],
    )

    return LaunchDescription([
        driver_node,
        filter_node,
    ])
