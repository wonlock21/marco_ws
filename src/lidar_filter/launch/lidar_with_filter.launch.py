from launch import LaunchDescription
from launch_ros.actions import LifecycleNode, Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    ydlidar_share = get_package_share_directory('ydlidar_ros2_driver')

    params_file = os.path.join(
        ydlidar_share,
        'params',
        'ydlidar.yaml'
    )

    driver_node = LifecycleNode(
        package='ydlidar_ros2_driver',
        executable='ydlidar_ros2_driver_node',
        name='ydlidar_ros2_driver_node',
        output='screen',
        emulate_tty=True,
        parameters=[params_file],
        namespace='/',
        remappings=[
            ('scan', 'scan_raw'),
        ],
    )

    tf2_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_tf_pub_laser',
        arguments=[
            '0', '0', '0.02',
            '0', '0', '0', '1',
            'base_link',
            'laser_frame'
        ],
    )

    filter_node = Node(
        package='lidar_filter',
        executable='self_scan_filter',
        name='self_scan_filter',
        output='screen',
    )

    return LaunchDescription([
        driver_node,
        tf2_node,
        filter_node,
    ])
