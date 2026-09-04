#!/usr/bin/env python3
"""One visible Phase 8 Nav2/route obstacle acceptance run."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    safety_share = get_package_share_directory('marco_safety')
    navigation_share = get_package_share_directory('marco_navigation')
    route_bt = os.path.join(
        navigation_share, 'behavior_trees', 'navigate_route_wait.xml')
    route_stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            navigation_share, 'launch', 'simulation_route.launch.py')),
        launch_arguments={
            'gazebo_gui': 'true', 'rviz': 'true',
            'software_gazebo_server': 'true',
            'software_gazebo_gui': 'true',
            'auto_initial_pose': 'true', 'auto_route': 'false',
            'run_acceptance': 'false', 'run_final_acceptance': 'false',
            'cmd_vel_output': '/cmd_vel_raw',
        }.items())
    safety = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            safety_share, 'launch', 'safety.launch.py')),
        launch_arguments={
            'use_sim_time': 'true', 'scan_topic': '/scan',
            'require_base_communication': 'false',
            'obstacle_wait_timeout_s': '0.0',
        }.items())
    acceptance = Node(
        package='marco_safety',
        executable='nav_action_obstacle_acceptance.py',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'result_path': LaunchConfiguration('result_path'),
            'route_bt': route_bt,
            'obstacle_hold_s': LaunchConfiguration('obstacle_hold_s'),
        }])
    return LaunchDescription([
        DeclareLaunchArgument('obstacle_hold_s', default_value='5.0'),
        DeclareLaunchArgument(
            'result_path',
            default_value='/tmp/marco_phase8/nav_action_obstacle.json'),
        route_stack, safety,
        TimerAction(period=20.0, actions=[acceptance]),
    ])
