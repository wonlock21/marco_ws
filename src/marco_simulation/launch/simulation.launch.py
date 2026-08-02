#!/usr/bin/env python3
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def gazebo_gui(context):
    if LaunchConfiguration('gazebo_gui').perform(context).lower() != 'true':
        return []
    env = os.environ.copy()
    if LaunchConfiguration('software_gazebo_gui').perform(context).lower() == 'true':
        env['LIBGL_ALWAYS_SOFTWARE'] = '1'
    return [TimerAction(period=3.0, actions=[ExecuteProcess(
        cmd=['ign', 'gazebo', '-g'], output='screen', additional_env=env
    )])]


def generate_launch_description():
    share = get_package_share_directory('marco_simulation')
    world = os.path.join(share, 'worlds', 'marco_test.sdf')
    xacro_file = os.path.join(share, 'urdf', 'marco_sim.urdf.xacro')
    rviz_config = os.path.join(share, 'config', 'marco_simulation.rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

    # Fortress Ogre2 crashes on WSLg's D3D12 texture-copy path. Sensors need
    # Ogre2 (Ogre1 returns range_min for every GPU-lidar ray), so only Gazebo's
    # rendering process uses llvmpipe. RViz keeps the normal WSLg renderer.
    server_env = os.environ.copy()
    server_env['LIBGL_ALWAYS_SOFTWARE'] = '1'
    server = ExecuteProcess(cmd=['ign', 'gazebo', '-s', '-r', world],
                            output='screen', additional_env=server_env)
    rsp = Node(package='robot_state_publisher', executable='robot_state_publisher',
               parameters=[{'robot_description': robot_description, 'use_sim_time': use_sim_time}],
               output='screen')
    spawn = Node(package='ros_gz_sim', executable='create', output='screen',
                 arguments=['-name', 'marco', '-topic', 'robot_description',
                            '-x', '0', '-y', '0', '-z', '0'])
    bridge = Node(package='ros_gz_bridge', executable='parameter_bridge', output='screen',
                  arguments=[
                      '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
                      '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
                      '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                      '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                      '/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
                      '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
                      '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
                      '/world/marco_test/model/marco/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model',
                  ],
                  remappings=[('/world/marco_test/model/marco/joint_state', '/joint_states')])
    rviz = Node(package='rviz2', executable='rviz2', arguments=['-d', rviz_config],
                parameters=[{'use_sim_time': use_sim_time}],
                condition=IfCondition(LaunchConfiguration('rviz')), output='screen')
    drive = Node(package='marco_simulation', executable='visual_test_drive.py',
                 parameters=[{'use_sim_time': use_sim_time}],
                 condition=IfCondition(LaunchConfiguration('visual_test')), output='screen')

    return LaunchDescription([
        DeclareLaunchArgument('gazebo_gui', default_value='false'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('visual_test', default_value='false'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('software_gazebo_gui', default_value='false'),
        server, rsp, bridge,
        TimerAction(period=2.0, actions=[spawn]),
        TimerAction(period=4.0, actions=[rviz]),
        TimerAction(period=5.0, actions=[drive]),
        OpaqueFunction(function=gazebo_gui),
    ])
