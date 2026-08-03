#!/usr/bin/env python3
"""WSL/Fortress Phase 8 stack; hardware launch/config remains untouched."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    simulation = get_package_share_directory('marco_simulation')
    safety = get_package_share_directory('marco_safety')
    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(simulation, 'launch', 'simulation.launch.py')),
        launch_arguments={
            'gazebo_gui': LaunchConfiguration('gazebo_gui'),
            'rviz': LaunchConfiguration('rviz'),
            'software_gazebo_server': 'true',
            'software_gazebo_gui': 'true',
            'visual_test': 'false',
            'use_sim_time': 'true',
        }.items())
    scan_gate = Node(
        package='marco_navigation', executable='simulation_scan_gate.py',
        output='screen', parameters=[{'use_sim_time': True}])
    service_bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        name='phase8_simulation_service_bridge', output='screen',
        arguments=[
            '/world/marco_test/create@ros_gz_interfaces/srv/SpawnEntity',
            '/world/marco_test/remove@ros_gz_interfaces/srv/DeleteEntity'])
    safe = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(safety, 'launch', 'safety.launch.py')),
        launch_arguments={
            'use_sim_time': 'true', 'scan_topic': '/scan_nav2',
            'base_frame': LaunchConfiguration('base_frame'),
            'obstacle_wait_timeout_s': LaunchConfiguration('obstacle_wait_timeout_s'),
        }.items())
    acceptance = Node(
        package='marco_safety', executable='phase8_acceptance.py', output='screen',
        parameters=[{'use_sim_time': True,
                     'result_path': LaunchConfiguration('result_path'),
                     'fault_scenario': LaunchConfiguration('fault_scenario')}],
        condition=IfCondition(LaunchConfiguration('run_acceptance')))
    return LaunchDescription([
        DeclareLaunchArgument('gazebo_gui', default_value='false'),
        DeclareLaunchArgument('rviz', default_value='false'),
        DeclareLaunchArgument('base_frame', default_value='base_footprint'),
        DeclareLaunchArgument('obstacle_wait_timeout_s', default_value='8.0'),
        DeclareLaunchArgument('run_acceptance', default_value='true'),
        DeclareLaunchArgument(
            'result_path', default_value='/tmp/marco_phase8/headless.json'),
        DeclareLaunchArgument('fault_scenario', default_value=''),
        sim, scan_gate, service_bridge, safe,
        TimerAction(period=5.0, actions=[acceptance]),
    ])
