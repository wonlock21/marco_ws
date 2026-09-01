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
    lane_share = get_package_share_directory("lane_tracking")
    bridge = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, "launch", "gui_bridge.launch.py")
        ),
        launch_arguments={"port": LaunchConfiguration("rosbridge_port")}.items(),
    )
    front_camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(lane_share, "launch", "front_camera.launch.py")
        ),
        launch_arguments={
            "camera": LaunchConfiguration("camera"),
            "web_stream": LaunchConfiguration("camera_web_stream"),
            "web_video_port": LaunchConfiguration("camera_web_port"),
        }.items(),
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
            "obstacle_detection_enabled": ParameterValue(
                LaunchConfiguration("obstacle_detection"), value_type=bool
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
    route_editor = Node(
        package="marco_route",
        executable="route_editor",
        name="route_editor",
        output="screen",
        parameters=[{
            "data_root": LaunchConfiguration("data_root"),
            "competition_profile": True,
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
    buzzer_driver = Node(
        package="marco_localization",
        executable="buzzer_driver.py",
        name="buzzer_driver",
        output="screen",
        parameters=[{
            "wpi_pin": ParameterValue(
                LaunchConfiguration("buzzer_wpi_pin"), value_type=int
            ),
            "active_high": ParameterValue(
                LaunchConfiguration("buzzer_active_high"), value_type=bool
            ),
            "on_time_s": ParameterValue(
                LaunchConfiguration("buzzer_on_time"), value_type=float
            ),
            "off_time_s": ParameterValue(
                LaunchConfiguration("buzzer_off_time"), value_type=float
            ),
            "dry_run": ParameterValue(
                LaunchConfiguration("buzzer_dry_run"), value_type=bool
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
        DeclareLaunchArgument(
            "camera", default_value="/dev/marco_front_camera"
        ),
        DeclareLaunchArgument("camera_web_stream", default_value="true"),
        DeclareLaunchArgument("camera_web_port", default_value="8080"),
        DeclareLaunchArgument(
            "demo_odom_topic", default_value="/odometry/filtered"
        ),
        DeclareLaunchArgument("turn_direction", default_value="1"),
        DeclareLaunchArgument("rosbridge_port", default_value="9090"),
        # Orange Pi 5 Plus fiziksel pin 7 = GPIO1_D6 = wiringOP pin 2.
        DeclareLaunchArgument("buzzer_wpi_pin", default_value="2"),
        DeclareLaunchArgument("buzzer_active_high", default_value="true"),
        DeclareLaunchArgument("buzzer_on_time", default_value="0.40"),
        DeclareLaunchArgument("buzzer_off_time", default_value="0.25"),
        DeclareLaunchArgument("buzzer_dry_run", default_value="false"),
        bridge,
        front_camera,
        manager,
        localization_manager,
        route_editor,
        demo_manager,
        buzzer_driver,
    ])
