"""SLAM Toolbox ile 2D haritalama.

Zincir:
  localization.launch.py  (robot + LiDAR + EKF, TF EKF'de)
  + async_slam_toolbox_node  (map -> odom)

Ornekler:
  ros2 launch marco_localization mapping.launch.py sahte:=true lidar:=true
  ros2 launch marco_localization mapping.launch.py lidar:=true

Surerek haritalamak icin AYRI terminal:
  ros2 run teleop_twist_keyboard teleop_twist_keyboard

Haritayi kaydetmek (ayri terminal):
  ros2 run marco_localization harita_kaydet.sh [isim]

pwm_bridge ile AYNI ANDA CALISTIRILAMAZ. pwm_bridge /odom yayinlamaz ve
seri portu base_driver ile paylasamaz. Mapping oncesi:
  pkill -f 'pwm[_bridge]|marco_pwm'
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _uyari(context, *args, **kwargs):
    """RViz + LiDAR birlikte acilirsa CPU acligini hatirlat."""
    lidar = LaunchConfiguration("lidar").perform(context).lower() in ("true", "1")
    rviz = LaunchConfiguration("rviz").perform(context).lower() in ("true", "1")
    if not (lidar and rviz):
        return []
    return [
        LogInfo(msg="=" * 72),
        LogInfo(msg="UYARI: mapping sirasinda RViz Orange Pi'de ACILMAMALI."),
        LogInfo(msg="/scan bozulur, harita catlak cikar. Kayit al veya uzak"),
        LogInfo(msg="makinede viewer.launch.py / mapping.rviz kullan."),
        LogInfo(msg="=" * 72),
    ]


def generate_launch_description() -> LaunchDescription:
    localization_share = get_package_share_directory("marco_localization")
    slam_config = os.path.join(localization_share, "config", "slam_toolbox.yaml")
    rviz_config = os.path.join(localization_share, "config", "mapping.rviz")

    arguments = [
        DeclareLaunchArgument("sahte", default_value="false"),
        DeclareLaunchArgument(
            "lidar",
            default_value="true",
            description="YDLidar Tmini Pro (haritalama icin varsayilan acik)",
        ),
        DeclareLaunchArgument("imu", default_value="false"),
        DeclareLaunchArgument("serial_port", default_value="/dev/marco_stm32"),
        DeclareLaunchArgument("lidar_port", default_value="/dev/ttyUSB0"),
        DeclareLaunchArgument(
            "rviz",
            default_value="false",
            description="Orange Pi'de KAPALI tut; uzak makinede ac",
        ),
    ]

    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(localization_share, "launch", "localization.launch.py")
        ),
        launch_arguments={
            "sahte": LaunchConfiguration("sahte"),
            "lidar": LaunchConfiguration("lidar"),
            "imu": LaunchConfiguration("imu"),
            "serial_port": LaunchConfiguration("serial_port"),
            "lidar_port": LaunchConfiguration("lidar_port"),
            "rviz": "false",
        }.items(),
    )

    # async: scan callback ayri thread'de; 10 Hz LiDAR'i bloklamaz.
    slam = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        output="screen",
        parameters=[slam_config],
    )

    map_preview = Node(
        package="marco_localization",
        executable="map_preview.py",
        name="map_preview",
        output="screen",
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config],
        condition=IfCondition(LaunchConfiguration("rviz")),
    )

    return LaunchDescription(
        arguments
        + [
            OpaqueFunction(function=_uyari),
            localization,
            slam,
            map_preview,
            rviz,
            LogInfo(msg="Surmek: ros2 run teleop_twist_keyboard teleop_twist_keyboard"),
            LogInfo(msg="Kaydet: ros2 run marco_localization harita_kaydet.sh <isim>"),
        ]
    )
