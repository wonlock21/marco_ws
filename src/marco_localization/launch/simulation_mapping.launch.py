#!/usr/bin/env python3
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    local_share = get_package_share_directory('marco_localization')
    sim_share = get_package_share_directory('marco_simulation')
    use_sim_time = LaunchConfiguration('use_sim_time')
    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(sim_share, 'launch',
                                                   'simulation.launch.py')),
        launch_arguments={
            'simulation_rviz': 'false', 'simulation_visual_test': 'false',
            'gazebo_gui': LaunchConfiguration('gazebo_gui'),
            'software_gazebo_server': LaunchConfiguration('software_gazebo_server'),
            'software_gazebo_gui': LaunchConfiguration('software_gazebo_gui'),
            'gazebo_gpu_adapter': LaunchConfiguration('gazebo_gpu_adapter'),
            'use_sim_time': use_sim_time,
        }.items())
    slam = Node(package='slam_toolbox', executable='async_slam_toolbox_node',
                name='slam_toolbox', output='screen', parameters=[
                    os.path.join(local_share, 'config', 'slam_toolbox_sim.yaml'),
                    {'use_sim_time': use_sim_time}])
    rviz = Node(package='rviz2', executable='rviz2', output='screen',
                arguments=['-d', os.path.join(local_share, 'config',
                                              'mapping_simulation.rviz')],
                parameters=[{'use_sim_time': use_sim_time}],
                condition=IfCondition(LaunchConfiguration('rviz')))
    drive = Node(package='marco_localization', executable='slam_test_drive.py',
                 output='screen', parameters=[{'use_sim_time': use_sim_time}],
                 condition=IfCondition(LaunchConfiguration('auto_drive')))
    acceptance = Node(package='marco_localization', executable='slam_acceptance.py',
                      output='screen', parameters=[
                          {'use_sim_time': use_sim_time,
                           'save_map': ParameterValue(
                               LaunchConfiguration('save_map'), value_type=bool),
                           'map_output': LaunchConfiguration('map_output'),
                           'result_path': LaunchConfiguration('result_path'),
                           'timeout': ParameterValue(
                               LaunchConfiguration('acceptance_timeout'),
                               value_type=float)}],
                      condition=IfCondition(LaunchConfiguration('run_acceptance')))
    return LaunchDescription([
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('gazebo_gui', default_value='false'),
        DeclareLaunchArgument('software_gazebo_server', default_value='true'),
        DeclareLaunchArgument('software_gazebo_gui', default_value='true'),
        DeclareLaunchArgument('gazebo_gpu_adapter', default_value='NVIDIA'),
        DeclareLaunchArgument('auto_drive', default_value='true'),
        DeclareLaunchArgument('run_acceptance', default_value='true'),
        DeclareLaunchArgument('save_map', default_value='true'),
        DeclareLaunchArgument('map_output', default_value='/tmp/marco_phase4/marco_test'),
        DeclareLaunchArgument('result_path', default_value='/tmp/marco_phase4_acceptance.json'),
        DeclareLaunchArgument('acceptance_timeout', default_value='240.0'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        simulation,
        TimerAction(period=6.0, actions=[slam]),
        TimerAction(period=8.0, actions=[rviz]),
        TimerAction(period=8.0, actions=[drive, acceptance]),
    ])
