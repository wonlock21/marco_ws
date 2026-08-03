"""Docking-control simulation with explicit ground-truth test inputs."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    simulation = get_package_share_directory('marco_simulation')
    safety = get_package_share_directory('marco_safety')
    docking = get_package_share_directory('marco_docking')
    use_sim_time = LaunchConfiguration('use_sim_time')
    sim = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        os.path.join(simulation, 'launch', 'simulation.launch.py')),
        launch_arguments={'gazebo_gui': LaunchConfiguration('gazebo_gui'),
                          'rviz': LaunchConfiguration('rviz'),
                          'software_gazebo_server': 'true',
                          'software_gazebo_gui': 'true',
                          'use_sim_time': use_sim_time}.items())
    safe = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        os.path.join(safety, 'launch', 'safety.launch.py')),
        launch_arguments={'use_sim_time': use_sim_time, 'scan_topic': '/scan'}.items())
    sim_inputs = Node(
        package='marco_docking', executable='phase9_sim_inputs', output='screen',
        parameters=[{'use_sim_time': use_sim_time,
                     'target_stop_distance_m': 0.75}])
    dock = Node(package='marco_docking', executable='dock_server', output='screen',
                parameters=[os.path.join(docking, 'config', 'docking.yaml'),
                            {'use_sim_time': use_sim_time}])
    service_bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        name='phase9_set_pose_bridge', output='screen',
        arguments=['/world/marco_test/set_pose@ros_gz_interfaces/srv/SetEntityPose'])
    visualizer = Node(package='marco_docking', executable='phase9_visualizer',
                      output='screen', parameters=[{'use_sim_time': use_sim_time}])
    return LaunchDescription([
        DeclareLaunchArgument('gazebo_gui', default_value='false'),
        DeclareLaunchArgument('rviz', default_value='false'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        sim, safe, sim_inputs, dock, service_bridge, visualizer])
