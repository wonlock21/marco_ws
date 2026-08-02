"""Faz 3 sahte donanim odometri/EKF kabul zincirini tek komutla baslatir."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    RegisterEventHandler,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.event_handlers import OnProcessExit
from launch_ros.actions import Node


def setup(context, *args, **kwargs):
    """Senaryo adini mevcut fake STM32 parametrelerine cevir."""
    scenario = LaunchConfiguration("scenario").perform(context)
    rviz_enabled = LaunchConfiguration("rviz").perform(context)
    scenarios = {
        "nominal": ("0.0", "0.0", "0.0"),
        "scale_error": ("0.05", "0.05", "0.0"),
        "separation_error": ("0.0", "0.0", "0.520"),
    }
    if scenario not in scenarios:
        raise ValueError("scenario nominal/scale_error/separation_error olmali")
    left, right, actual_separation = scenarios[scenario]
    share = get_package_share_directory("marco_localization")

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(share, "launch", "localization.launch.py")),
        launch_arguments={
            "sahte": "true", "rviz": "false", "lidar": "false",
            "imu": LaunchConfiguration("imu"),
            "fake_wheel_scale_error_left": left,
            "fake_wheel_scale_error_right": right,
            "fake_wheel_separation_actual": actual_separation,
        }.items(),
    )
    fake_imu = Node(
        package="marco_localization", executable="fake_imu.py", output="screen",
        condition=IfCondition(LaunchConfiguration("imu")),
    )
    rviz = Node(
        package="rviz2", executable="rviz2",
        arguments=["-d", os.path.join(share, "config", "odometry_test.rviz")],
        # Include edilen localization launch'i kendi rviz argumanini false
        # yapar. Degeri include calismadan once yakalayarak kapsam sizintisinin
        # kabul RViz'ini kapatmasini onleriz.
        condition=IfCondition(rviz_enabled),
    )
    paths = Node(
        package="marco_localization", executable="odometry_paths.py", output="screen",
    )
    test = Node(
        package="marco_localization", executable="odometry_check.py", output="screen",
        arguments=[
            "--test", "kabul", "--distance", LaunchConfiguration("distance"),
            "--turn-deg", LaunchConfiguration("turn_deg"), "--scenario", scenario,
        ],
        condition=IfCondition(LaunchConfiguration("run_test")),
    )
    completed = RegisterEventHandler(
        OnProcessExit(
            target_action=test,
            on_exit=[LogInfo(msg=(
                "Faz 3 nominal görsel test tamamlandı. Robot durduruldu; RViz "
                "inceleme için açık bırakıldı. Ctrl+C ile kapatabilirsiniz."
            ))],
        )
    )
    return [
        localization, fake_imu, paths, rviz, completed,
        TimerAction(period=3.0, actions=[test]),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("rviz", default_value="true"),
        DeclareLaunchArgument("imu", default_value="false"),
        DeclareLaunchArgument("scenario", default_value="nominal"),
        DeclareLaunchArgument("run_test", default_value="true"),
        DeclareLaunchArgument("distance", default_value="10.0"),
        DeclareLaunchArgument("turn_deg", default_value="360.0"),
        OpaqueFunction(function=setup),
    ])
