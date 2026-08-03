#!/usr/bin/env python3
"""Simulator-only Phase 7 route acceptance; reuses the Phase 6 stack exactly once."""
import os
import subprocess

from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def setup(context):
    share = get_package_share_directory('marco_navigation')
    graph = os.path.join(share, 'graphs', 'marco_test_route.geojson')
    map_yaml = os.path.join(get_package_share_directory('marco_localization'),
                            'simulation_test_maps', 'marco_test', 'marco_test.yaml')
    validator = os.path.join(get_package_prefix('marco_navigation'), 'lib',
                             'marco_navigation', 'route_graph_validator.py')
    result_dir = '/tmp/marco_phase7'
    os.makedirs(result_dir, exist_ok=True)
    checked = subprocess.run([validator, graph, '--map', map_yaml,
                              '--result', os.path.join(result_dir, 'launch_graph_validation.json')],
                             check=False, capture_output=True, text=True)
    if checked.returncode:
        raise RuntimeError('Simulation route graph rejected: ' + checked.stderr.strip())

    phase6 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(share, 'launch', 'simulation_navigation.launch.py')),
        launch_arguments={
            'map': LaunchConfiguration('map'), 'rviz': 'false',
            'gazebo_gui': LaunchConfiguration('gazebo_gui'),
            'software_gazebo_server': LaunchConfiguration('software_gazebo_server'),
            'software_gazebo_gui': LaunchConfiguration('software_gazebo_gui'),
            'gazebo_gpu_adapter': LaunchConfiguration('gazebo_gpu_adapter'),
            'auto_initial_pose': LaunchConfiguration('auto_initial_pose'),
            'auto_navigation': 'false', 'run_acceptance': 'false',
            'goal_scenario': 'route',
            'navigate_to_pose_bt': os.path.join(share, 'behavior_trees', 'navigate_route_wait.xml'),
            'cmd_vel_output': LaunchConfiguration('cmd_vel_output'),
            'use_sim_time': 'true'}.items())
    route = Node(package='nav2_route', executable='route_server', name='route_server', output='screen',
                 parameters=[os.path.join(share, 'config', 'route_server_sim.yaml'),
                             {'use_sim_time': True, 'graph_filepath': graph}],
                 # Keep the installed percentage-oriented operation observable;
                 # route_test_mission publishes the graph's absolute m/s limit.
                 remappings=[('/abs_speed_limit', '/route_speed_limit_raw')])
    lifecycle = Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
                     name='lifecycle_manager_route', output='screen', parameters=[{
                         'use_sim_time': True, 'autostart': True,
                         'node_names': ['route_server'], 'bond_timeout': 0.0}])
    scorer_nodes = []
    for namespace, config in (('distance', 'route_server_distance_sim.yaml'),
                              ('time', 'route_server_time_sim.yaml')):
        scorer_nodes += [
            Node(package='nav2_route', executable='route_server', name='route_server',
                 namespace=namespace, output='screen', parameters=[os.path.join(share, 'config', config),
                 {'use_sim_time': True, 'graph_filepath': graph}]),
            Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
                 name='lifecycle_manager_route', namespace=namespace, output='screen', parameters=[{
                     'use_sim_time': True, 'autostart': True,
                     'node_names': ['route_server'], 'bond_timeout': 0.0}])]
    common = [{'use_sim_time': True, 'scenario': LaunchConfiguration('route_scenario'),
               'result_path': LaunchConfiguration('result_path'), 'graph': graph}]
    mission = Node(package='marco_navigation', executable='route_test_mission.py', output='screen',
                   parameters=common)
    acceptance = Node(package='marco_navigation', executable='route_acceptance.py', output='screen',
                      parameters=common)
    visualizer = Node(package='marco_navigation', executable='route_graph_visualizer.py', output='screen',
                      parameters=[{'use_sim_time': True, 'graph': graph}])
    rviz = Node(package='rviz2', executable='rviz2', name='simulation_route_rviz', output='screen',
                arguments=['-d', os.path.join(share, 'config', 'route_simulation.rviz')],
                parameters=[{'use_sim_time': True}])
    actions = [phase6, route, lifecycle, visualizer]
    if LaunchConfiguration('run_final_acceptance').perform(context).lower() == 'true':
        actions += scorer_nodes
        actions.append(TimerAction(period=16.0, actions=[Node(
            package='marco_navigation', executable='phase7_final_acceptance.py', output='screen',
            parameters=[{'use_sim_time': True, 'result_dir': result_dir,
                         'route_bt': os.path.join(share, 'behavior_trees', 'navigate_route_wait.xml')}])]))
    if LaunchConfiguration('run_acceptance').perform(context).lower() == 'true':
        actions += [TimerAction(period=12.0, actions=[acceptance]),
                    TimerAction(period=16.0, actions=[mission])]
    elif LaunchConfiguration('auto_route').perform(context).lower() == 'true':
        actions.append(TimerAction(period=16.0, actions=[mission]))
    if LaunchConfiguration('rviz').perform(context).lower() == 'true': actions.append(rviz)
    return actions


def generate_launch_description():
    args = [DeclareLaunchArgument('map', default_value=''),
            DeclareLaunchArgument('rviz', default_value='true'),
            DeclareLaunchArgument('gazebo_gui', default_value='false'),
            DeclareLaunchArgument('software_gazebo_server', default_value='true'),
            DeclareLaunchArgument('software_gazebo_gui', default_value='true'),
            DeclareLaunchArgument('gazebo_gpu_adapter', default_value='NVIDIA'),
            DeclareLaunchArgument('auto_initial_pose', default_value='true'),
            DeclareLaunchArgument('auto_route', default_value='false'),
            DeclareLaunchArgument('run_acceptance', default_value='false'),
            DeclareLaunchArgument('run_final_acceptance', default_value='false'),
            DeclareLaunchArgument('route_scenario', default_value='nominal'),
            DeclareLaunchArgument('result_path', default_value='/tmp/marco_phase7/final.json')]
    args.append(DeclareLaunchArgument('cmd_vel_output', default_value='/cmd_vel'))
    return LaunchDescription(args + [OpaqueFunction(function=setup)])
