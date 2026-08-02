#!/usr/bin/env python3
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, OpaqueFunction, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def gazebo_environment(context, software_argument):
    env = os.environ.copy()
    software = LaunchConfiguration(software_argument).perform(context).lower() == 'true'
    if software:
        env['LIBGL_ALWAYS_SOFTWARE'] = '1'
        env.pop('MESA_D3D12_DEFAULT_ADAPTER_NAME', None)
    else:
        env.pop('LIBGL_ALWAYS_SOFTWARE', None)
        adapter = LaunchConfiguration('gazebo_gpu_adapter').perform(context)
        if adapter:
            env['MESA_D3D12_DEFAULT_ADAPTER_NAME'] = adapter
        else:
            env.pop('MESA_D3D12_DEFAULT_ADAPTER_NAME', None)
    return env


def gazebo_server(context, world):
    return [ExecuteProcess(
        cmd=['ign', 'gazebo', '-s', '-r', world], output='screen',
        additional_env=gazebo_environment(context, 'software_gazebo_server')
    )]


def gazebo_gui(context):
    if LaunchConfiguration('gazebo_gui').perform(context).lower() != 'true':
        return []
    return [TimerAction(period=3.0, actions=[ExecuteProcess(
        cmd=['ign', 'gazebo', '-g'], output='screen',
        additional_env=gazebo_environment(context, 'software_gazebo_gui')
    )])]


def generate_launch_description():
    share = get_package_share_directory('marco_simulation')
    world = os.path.join(share, 'worlds', 'marco_test.sdf')
    xacro_file = os.path.join(share, 'urdf', 'marco_sim.urdf.xacro')
    rviz_config = os.path.join(share, 'config', 'marco_simulation.rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

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
        DeclareLaunchArgument(
            'software_gazebo_server', default_value='false',
            description='Use llvmpipe software rendering for the Gazebo server only.'),
        DeclareLaunchArgument(
            'software_gazebo_gui', default_value='false',
            description='Use llvmpipe software rendering for the Gazebo GUI only.'),
        DeclareLaunchArgument(
            'gazebo_gpu_adapter', default_value='NVIDIA',
            description='MESA D3D12 adapter name for GPU-mode Gazebo processes; empty disables it.'),
        DeclareLaunchArgument(
            'gazebo_gui', default_value='true',
            description='Start the Gazebo graphical client.'),
        DeclareLaunchArgument(
            'rviz', default_value='true',
            description='Start RViz with its normal inherited renderer environment.'),
        DeclareLaunchArgument(
            'visual_test', default_value='false',
            description='Run the automatic visual driving route.'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use the Gazebo simulation clock in ROS nodes.'),
        OpaqueFunction(function=gazebo_server, args=[world]), rsp, bridge,
        TimerAction(period=2.0, actions=[spawn]),
        TimerAction(period=4.0, actions=[rviz]),
        TimerAction(period=5.0, actions=[drive]),
        OpaqueFunction(function=gazebo_gui),
    ])
