#!/usr/bin/env python3
"""Single-command WSL Fortress AMCL simulation localization acceptance."""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def resolve_map(context):
    value = LaunchConfiguration('map').perform(context)
    if not value:
        value = os.path.join(get_package_share_directory('marco_localization'),
                             'simulation_test_maps', 'marco_test', 'marco_test.yaml')
    value = os.path.abspath(os.path.expanduser(value))
    if not os.path.isfile(value):
        raise FileNotFoundError('Simulation test map YAML not found: %s' % value)
    share = get_package_share_directory('marco_localization')
    params = os.path.join(share, 'config', 'amcl_sim.yaml')
    use_sim = {'use_sim_time': True}
    map_server = Node(package='nav2_map_server', executable='map_server', name='map_server',
                      output='screen', parameters=[params, use_sim, {'yaml_filename': value}])
    amcl = Node(package='nav2_amcl', executable='amcl', name='amcl', output='screen',
                parameters=[params, use_sim])
    lifecycle = Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
                     name='lifecycle_manager_localization', output='screen', parameters=[params, use_sim])
    truth = Node(package='marco_localization', executable='ground_truth_pose.py',
                 output='screen', parameters=[use_sim, {'map_world_x': 0.0, 'map_world_y': 0.0,
                                                        'map_world_yaw': 0.0}])
    initial = Node(package='marco_localization', executable='amcl_initial_pose.py', output='screen',
                   condition=IfCondition(LaunchConfiguration('auto_initial_pose')),
                   parameters=[use_sim, {'initial_x': ParameterValue(LaunchConfiguration('initial_x'), value_type=float),
                                         'initial_y': ParameterValue(LaunchConfiguration('initial_y'), value_type=float),
                                         'initial_yaw': ParameterValue(LaunchConfiguration('initial_yaw'), value_type=float)}])
    drive = Node(package='marco_localization', executable='amcl_test_drive.py', output='screen',
                 condition=IfCondition(LaunchConfiguration('auto_drive')), parameters=[use_sim])
    accept = Node(package='marco_localization', executable='amcl_acceptance.py', output='screen',
                  condition=IfCondition(LaunchConfiguration('run_acceptance')),
                  parameters=[use_sim, {'result_path': LaunchConfiguration('result_path'),
                                        'require_drive': ParameterValue(LaunchConfiguration('auto_drive'), value_type=bool),
                                        'timeout': ParameterValue(LaunchConfiguration('acceptance_timeout'), value_type=float)}])
    rviz = Node(package='rviz2', executable='rviz2', name='simulation_localization_test_rviz',
                arguments=['-d', os.path.join(share, 'config', 'localization_simulation.rviz')],
                parameters=[use_sim], condition=IfCondition(LaunchConfiguration('rviz')), output='screen')
    return [map_server, amcl, lifecycle, truth,
            TimerAction(period=7.0, actions=[accept]),
            TimerAction(period=8.0, actions=[initial]),
            TimerAction(period=18.0, actions=[rviz]),
            TimerAction(period=14.0, actions=[drive])]


def generate_launch_description():
    sim_share = get_package_share_directory('marco_simulation')
    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(sim_share, 'launch', 'simulation.launch.py')),
        launch_arguments={'simulation_rviz':'false', 'simulation_visual_test':'false',
                          'gazebo_gui':LaunchConfiguration('gazebo_gui'),
                          'software_gazebo_server':LaunchConfiguration('software_gazebo_server'),
                          'software_gazebo_gui':LaunchConfiguration('software_gazebo_gui'),
                          'gazebo_gpu_adapter':LaunchConfiguration('gazebo_gpu_adapter'),
                          'use_sim_time':'true'}.items())
    args = [
        DeclareLaunchArgument('map', default_value='', description='Simulation test map YAML; empty uses packaged marco_test.'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('gazebo_gui', default_value='false'),
        DeclareLaunchArgument('software_gazebo_server', default_value='true'),
        DeclareLaunchArgument('software_gazebo_gui', default_value='true'),
        DeclareLaunchArgument('gazebo_gpu_adapter', default_value='NVIDIA'),
        DeclareLaunchArgument('initial_x', default_value='0.0'),
        DeclareLaunchArgument('initial_y', default_value='0.0'),
        DeclareLaunchArgument('initial_yaw', default_value='0.0'),
        DeclareLaunchArgument('auto_initial_pose', default_value='true'),
        DeclareLaunchArgument('auto_drive', default_value='true'),
        DeclareLaunchArgument('run_acceptance', default_value='true'),
        DeclareLaunchArgument('acceptance_timeout', default_value='300.0'),
        DeclareLaunchArgument('result_path', default_value='/tmp/marco_phase5_acceptance.json')]
    return LaunchDescription(args + [simulation, OpaqueFunction(function=resolve_map)])
