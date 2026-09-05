"""Phase-10 mission layer. Production default is the existing ROS PLC contract."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    graph = os.path.join(get_package_share_directory('marco_navigation'), 'graphs',
                         'phase10_route.geojson')
    source = LaunchConfiguration('task_source')
    test_lift = LaunchConfiguration('test_only_lift')
    qr_adapter = LaunchConfiguration('qr_reader_adapter')
    return LaunchDescription([
        DeclareLaunchArgument('task_source', default_value='plc',
                              description='plc (production) or mock_plc (simulation)'),
        DeclareLaunchArgument('manual_task_enabled', default_value='true'),
        DeclareLaunchArgument('simulate_steps', default_value='false'),
        DeclareLaunchArgument('graph_file', default_value=graph),
        DeclareLaunchArgument('gate_node', default_value='kapi_q5'),
        DeclareLaunchArgument('return_gate_node', default_value='kapi_q6'),
        DeclareLaunchArgument('require_active_field', default_value='false'),
        DeclareLaunchArgument('require_safety_supervisor', default_value='true'),
        DeclareLaunchArgument('require_base_communication', default_value='true'),
        DeclareLaunchArgument(
            'imu', default_value='true',
            description='Mission manevra sagliginda IMU freshness zorunlulugu'),
        DeclareLaunchArgument('test_only_lift', default_value='false'),
        DeclareLaunchArgument('qr_reader_adapter', default_value='true'),
        Node(package='marco_mission', executable='qr_reader_adapter',
             name='qr_reader_adapter', output='screen',
             condition=IfCondition(qr_adapter)),
        Node(package='marco_mission', executable='mock_plc', name='mock_plc',
             output='screen',
             condition=IfCondition(PythonExpression(["'", source,
                                                     "' == 'mock_plc'"]))),
        Node(package='marco_mission', executable='test_lift_server',
             name='test_only_lift_server', output='screen',
             condition=IfCondition(test_lift), parameters=[{'test_only': True}]),
        Node(package='marco_mission', executable='mission_manager',
             name='mission_manager', output='screen', parameters=[{
                 'task_source': source,
                 'simulate_steps': LaunchConfiguration('simulate_steps'),
                 'manual_task_enabled': LaunchConfiguration('manual_task_enabled'),
                 'graph_file': LaunchConfiguration('graph_file'),
                 'gate_node': LaunchConfiguration('gate_node'),
                 'return_gate_node': LaunchConfiguration('return_gate_node'),
                 'require_active_field':
                     LaunchConfiguration('require_active_field'),
                 'require_safety_supervisor':
                     LaunchConfiguration('require_safety_supervisor'),
                 'require_base_communication':
                     LaunchConfiguration('require_base_communication'),
                 'imu_enabled': LaunchConfiguration('imu'),
             }]),
    ])
