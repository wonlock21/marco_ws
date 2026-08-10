"""Arayuz icin rosbridge, haritalama ve lokalizasyon kontrol dugumleri."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    bringup_share = get_package_share_directory("marco_bringup")
    bridge = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, "launch", "gui_bridge.launch.py")
        ),
        launch_arguments={"port": LaunchConfiguration("rosbridge_port")}.items(),
    )
    manager = Node(
        package="marco_localization",
        executable="mapping_manager.py",
        name="mapping_manager",
        output="screen",
        parameters=[{
            "fake_hardware": ParameterValue(
                LaunchConfiguration("sahte"), value_type=bool
            ),
            "use_imu": ParameterValue(
                LaunchConfiguration("imu"), value_type=bool
            ),
            "serial_port": LaunchConfiguration("serial_port"),
            "lidar_port": LaunchConfiguration("lidar_port"),
            "data_root": LaunchConfiguration("data_root"),
            "save_timeout": ParameterValue(
                LaunchConfiguration("save_timeout"), value_type=float
            ),
        }],
    )
    localization_manager = Node(
        package="marco_localization",
        executable="localization_manager.py",
        name="localization_manager",
        output="screen",
        parameters=[{
            "fake_hardware": ParameterValue(
                LaunchConfiguration("sahte"), value_type=bool
            ),
            "use_imu": ParameterValue(
                LaunchConfiguration("imu"), value_type=bool
            ),
            "obstacle_detection_enabled": ParameterValue(
                LaunchConfiguration("obstacle_detection"), value_type=bool
            ),
            "serial_port": LaunchConfiguration("serial_port"),
            "lidar_port": LaunchConfiguration("lidar_port"),
            "data_root": LaunchConfiguration("data_root"),
            "startup_timeout": ParameterValue(
                LaunchConfiguration("localization_timeout"), value_type=float
            ),
            "initial_pose_timeout": ParameterValue(
                LaunchConfiguration("initial_pose_timeout"), value_type=float
            ),
            "initial_pose_xy_std": ParameterValue(
                LaunchConfiguration("initial_pose_xy_std"), value_type=float
            ),
            "initial_pose_yaw_std": ParameterValue(
                LaunchConfiguration("initial_pose_yaw_std"), value_type=float
            ),
        }],
    )
    demo_manager = Node(
        package="marco_demo",
        executable="demo_scenario_manager",
        name="demo_scenario_manager",
        output="screen",
        parameters=[{
            "camera": LaunchConfiguration("camera"),
            "odom_topic": LaunchConfiguration("demo_odom_topic"),
            "data_root": LaunchConfiguration("data_root"),
            "turn_direction": ParameterValue(
                LaunchConfiguration("turn_direction"), value_type=int
            ),
            "obstacle_detection_enabled": ParameterValue(
                LaunchConfiguration("obstacle_detection"), value_type=bool
            ),
        }],
    )
    return LaunchDescription([
        DeclareLaunchArgument("sahte", default_value="false"),
        DeclareLaunchArgument("imu", default_value="true"),
        # Gecici hareket videosu bypass'i. Saha testinden sonra tekrar true yap.
        DeclareLaunchArgument("obstacle_detection", default_value="false"),
        DeclareLaunchArgument("serial_port", default_value="/dev/marco_stm32"),
        DeclareLaunchArgument("lidar_port", default_value="/dev/ttyUSB0"),
        DeclareLaunchArgument(
            "data_root", default_value="~/marco_data/fields"
        ),
        DeclareLaunchArgument("save_timeout", default_value="30.0"),
        DeclareLaunchArgument("localization_timeout", default_value="30.0"),
        DeclareLaunchArgument("initial_pose_timeout", default_value="35.0"),
        DeclareLaunchArgument("initial_pose_xy_std", default_value="0.25"),
        DeclareLaunchArgument(
            "initial_pose_yaw_std", default_value="0.174532925"
        ),
        DeclareLaunchArgument("camera", default_value="/dev/video0"),
        DeclareLaunchArgument(
            "demo_odom_topic", default_value="/odometry/filtered"
        ),
        DeclareLaunchArgument("turn_direction", default_value="1"),
        DeclareLaunchArgument("rosbridge_port", default_value="9090"),
        bridge,
        manager,
        localization_manager,
        demo_manager,
    ])
