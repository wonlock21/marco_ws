"""Kayitli harita uzerinde AMCL lokalizasyonu.

Zincir:
  localization.launch.py   (robot + LiDAR + EKF → odom→base_footprint)
  + map_server             (/map)
  + amcl                   (map→odom)
  + lifecycle_manager

slam_toolbox mapping ile AYNI ANDA CALISTIRMA.

Ornekler:
  ros2 launch marco_localization amcl.launch.py \\
      sahte:=true lidar:=true harita:=oda_test

  ros2 launch marco_localization amcl.launch.py \\
      sahte:=true lidar:=true harita:=oda_test \\
      baslangic:=true x:=0.0 y:=0.0 yaw:=0.0

  ros2 run marco_localization baslangic_poz.sh 0 0 0
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


def _harita_yolu(context) -> str:
    """harita argumanini mutlak yaml yoluna cevirir."""
    ad = LaunchConfiguration("harita").perform(context)
    if ad.endswith(".yaml") and os.path.isfile(ad):
        return os.path.abspath(ad)
    if os.path.isabs(ad):
        raise FileNotFoundError(f"Harita bulunamadi: {ad}")

    maps_dir = os.path.join(
        get_package_share_directory("marco_navigation"), "maps"
    )
    isim = f"{ad}.yaml" if not ad.endswith(".yaml") else ad
    adaylar = [
        os.path.join(maps_dir, isim),
        os.path.join(
            os.path.expanduser("~/marco_ws/src/marco_navigation/maps"), isim
        ),
    ]
    for yol in adaylar:
        if os.path.isfile(yol):
            return yol
    raise FileNotFoundError(
        f"Harita bulunamadi: {ad!r}. Aranan: {adaylar}. "
        "Once /mapping/save servisiyle saha haritasini kaydedin."
    )


def _kur(context, *args, **kwargs):
    localization_share = get_package_share_directory("marco_localization")
    amcl_config = os.path.join(localization_share, "config", "amcl.yaml")
    rviz_config = os.path.join(localization_share, "config", "amcl.rviz")

    harita_yaml = _harita_yolu(context)
    baslangic = LaunchConfiguration("baslangic").perform(context).lower() in (
        "true", "1", "yes",
    )

    robot = IncludeLaunchDescription(
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

    # yaml_filename'i dugume dogrudan ver — RewrittenYaml bos anahtar eklemez,
    # amcl.yaml'de yaml_filename yoktu ve map_server "not initialized" diyordu.
    map_server = Node(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        output="screen",
        parameters=[amcl_config, {"yaml_filename": harita_yaml}],
    )

    amcl_params = [amcl_config]
    if baslangic:
        amcl_params.append(
            {
                "set_initial_pose": True,
                "initial_pose": {
                    "x": float(LaunchConfiguration("x").perform(context)),
                    "y": float(LaunchConfiguration("y").perform(context)),
                    "z": 0.0,
                    "yaw": float(LaunchConfiguration("yaw").perform(context)),
                },
            }
        )

    amcl = Node(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        output="screen",
        parameters=amcl_params,
    )

    lifecycle = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_localization",
        output="screen",
        parameters=[amcl_config],
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config],
        condition=IfCondition(LaunchConfiguration("rviz")),
    )

    map_preview = Node(
        package="marco_localization",
        executable="map_preview.py",
        name="map_preview",
        output="screen",
    )

    mesajlar = [
        LogInfo(msg=f"Harita: {harita_yaml}"),
        LogInfo(
            msg=(
                "Baslangic pozu launch'tan yukleniyor."
                if baslangic
                else (
                    "Baslangic: ros2 run marco_localization "
                    "baslangic_poz.sh x y yaw_derece"
                )
            )
        ),
    ]

    return mesajlar + [robot, map_server, amcl, lifecycle, map_preview, rviz]


def generate_launch_description() -> LaunchDescription:
    arguments = [
        DeclareLaunchArgument("sahte", default_value="false"),
        DeclareLaunchArgument(
            "lidar",
            default_value="true",
            description="YDLidar Tmini Pro (AMCL icin varsayilan acik)",
        ),
        DeclareLaunchArgument("imu", default_value="false"),
        DeclareLaunchArgument("serial_port", default_value="/dev/marco_stm32"),
        DeclareLaunchArgument("lidar_port", default_value="/dev/ttyUSB0"),
        DeclareLaunchArgument(
            "rviz",
            default_value="false",
            description="Orange Pi'de KAPALI; uzak makinede ac",
        ),
        DeclareLaunchArgument(
            "harita",
            default_value="",
            description="maps/ altindaki isim (uzantisiz) veya mutlak .yaml yolu",
        ),
        DeclareLaunchArgument(
            "baslangic",
            default_value="false",
            description="true ise x/y/yaw ile AMCL'i hemen baslat",
        ),
        DeclareLaunchArgument("x", default_value="0.0"),
        DeclareLaunchArgument("y", default_value="0.0"),
        DeclareLaunchArgument(
            "yaw",
            default_value="0.0",
            description="Baslangic yonu RADYAN cinsinden",
        ),
    ]

    return LaunchDescription(arguments + [OpaqueFunction(function=_kur)])
