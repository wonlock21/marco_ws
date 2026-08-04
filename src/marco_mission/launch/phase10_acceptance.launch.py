"""Isolated headless Phase-10 acceptance (does not repeat Phase 6-9 suites)."""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    graph = os.path.join(get_package_share_directory('marco_navigation'), 'graphs',
                         'phase10_route.geojson')
    return LaunchDescription([
        Node(package='marco_mission', executable='mock_plc', output='screen',
             parameters=[{'gate_delay_s': 0.02}]),
        Node(package='marco_mission', executable='phase10_test_interfaces',
             output='screen'),
        Node(package='marco_mission', executable='mission_manager', output='screen',
             parameters=[{'task_source': 'mock_plc', 'manual_task_enabled': True,
                          'graph_file': graph, 'gate_timeout_s': 0.25,
                          'action_timeout_s': 2.0, 'plc_freshness_s': 0.6}]),
        Node(package='marco_mission', executable='phase10_acceptance',
             output='screen'),
    ])
