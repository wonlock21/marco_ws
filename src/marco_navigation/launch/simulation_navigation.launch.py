#!/usr/bin/env python3
"""Phase 6 Nav2 on the validated Phase 5 WSL/Fortress localization stack."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def setup(context):
    nav = get_package_share_directory('marco_navigation')
    loc = get_package_share_directory('marco_localization')
    bringup = get_package_share_directory('nav2_bringup')
    params_source = os.path.join(nav, 'config', 'nav2_sim_params.yaml')
    bt = LaunchConfiguration('navigate_to_pose_bt').perform(context)
    if not bt:
        bt = os.path.join(nav, 'behavior_trees', 'navigate_to_pose_sim_wait.xml')
    through_bt = os.path.join(nav, 'behavior_trees', 'navigate_through_poses_sim_wait.xml')
    with open(params_source, encoding='utf-8') as stream:
        params_text = stream.read()
    if LaunchConfiguration('goal_scenario').perform(context) == 'scan_loss':
        params_text = params_text.replace('topic: /scan\n', 'topic: /scan_nav2\n')
    if LaunchConfiguration('goal_scenario').perform(context) == 'planner_timeout':
        params_text = params_text.replace('max_planning_time: 5.0\n',
                                          'max_planning_time: 0.000001\n')
    if LaunchConfiguration('goal_scenario').perform(context) == 'route':
        # Route paths contain deliberate 90-degree node transitions. Keep the
        # Phase 6 default intact, but let the shim align at graph nodes here.
        params_text = params_text.replace('angular_dist_threshold: 3.14\n',
                                          'angular_dist_threshold: 0.60\n')
    marker = 'default_nav_to_pose_bt_xml: ""'
    through_marker = 'default_nav_through_poses_bt_xml: ""'
    if marker not in params_text or through_marker not in params_text:
        raise RuntimeError('BT path marker missing from nav2_sim_params.yaml')
    params_path = '/tmp/marco_nav2_sim_params_%s.yaml' % os.getpid()
    with open(params_path, 'w', encoding='utf-8') as stream:
        stream.write(params_text.replace(marker, 'default_nav_to_pose_bt_xml: "%s"' % bt)
                     .replace(through_marker, 'default_nav_through_poses_bt_xml: "%s"' % through_bt))

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(loc, 'launch', 'simulation_localization.launch.py')),
        launch_arguments={
            'map': LaunchConfiguration('map'), 'rviz': 'false',
            'gazebo_gui': LaunchConfiguration('gazebo_gui'),
            'software_gazebo_server': LaunchConfiguration('software_gazebo_server'),
            'software_gazebo_gui': LaunchConfiguration('software_gazebo_gui'),
            'gazebo_gpu_adapter': LaunchConfiguration('gazebo_gpu_adapter'),
            'auto_initial_pose': LaunchConfiguration('auto_initial_pose'),
            'auto_drive': 'false', 'run_acceptance': 'false',
        }.items())
    scan_gate = Node(package='marco_navigation', executable='simulation_scan_gate.py',
                     output='screen',
                     parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}])
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(bringup, 'launch', 'navigation_launch.py')),
        launch_arguments={'use_sim_time': LaunchConfiguration('use_sim_time'),
                          'params_file': params_path, 'autostart': 'true',
                          'use_composition': 'False', 'use_respawn': 'False'}.items())
    common = {'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool),
              'scenario': LaunchConfiguration('goal_scenario'),
              'timeout': ParameterValue(LaunchConfiguration('navigation_timeout'), value_type=float),
              'result_path': LaunchConfiguration('result_path')}
    goals = Node(package='marco_navigation', executable='nav2_test_goals.py', output='screen',
                 parameters=[common])
    acceptance = Node(package='marco_navigation', executable='nav2_acceptance.py', output='screen',
                      parameters=[common])
    simulation_services = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        name='navigation_simulation_service_bridge', output='screen',
        arguments=[
            '/world/marco_test/create@ros_gz_interfaces/srv/SpawnEntity',
            '/world/marco_test/remove@ros_gz_interfaces/srv/DeleteEntity'])
    rviz = Node(package='rviz2', executable='rviz2', name='simulation_navigation_rviz',
                arguments=['-d', os.path.join(nav, 'config', 'navigation_simulation.rviz')],
                parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
                output='screen')
    actions = [localization, scan_gate, nav2, simulation_services]
    if LaunchConfiguration('run_acceptance').perform(context).lower() == 'true':
        actions.append(acceptance)
    elif LaunchConfiguration('auto_navigation').perform(context).lower() == 'true':
        actions.append(TimerAction(period=1.0, actions=[goals]))
    # RViz must be a real, independently observable process in visible acceptance
    # runs.  Starting it directly also avoids tying its startup to simulation time.
    if LaunchConfiguration('rviz').perform(context).lower() == 'true':
        actions.append(rviz)
    return actions


def generate_launch_description():
    args = [
        DeclareLaunchArgument('map', default_value=''), DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('gazebo_gui', default_value='false'),
        DeclareLaunchArgument('software_gazebo_server', default_value='true'),
        DeclareLaunchArgument('software_gazebo_gui', default_value='true'),
        DeclareLaunchArgument('gazebo_gpu_adapter', default_value='NVIDIA'),
        DeclareLaunchArgument('auto_initial_pose', default_value='true'),
        DeclareLaunchArgument('auto_navigation', default_value='false'),
        DeclareLaunchArgument('run_acceptance', default_value='false'),
        DeclareLaunchArgument('goal_scenario', default_value='nominal'),
        DeclareLaunchArgument('navigate_to_pose_bt', default_value=''),
        DeclareLaunchArgument('result_path', default_value='/tmp/marco_phase6/acceptance.json'),
        DeclareLaunchArgument('navigation_timeout', default_value='600.0'),
        DeclareLaunchArgument('use_sim_time', default_value='true')]
    return LaunchDescription(args + [OpaqueFunction(function=setup)])
