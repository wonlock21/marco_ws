"""Robotun temel katmanini ayaga kaldirir: robot modeli + STM32 koprusu.

joint_state_publisher BILINCLI OLARAK CALISTIRILMAZ. O dugum URDF'teki
eklemler icin uydurma degerler yayinlar; base_driver ise encoderlardan gelen
gercek degerleri yayinlar. Ikisi birlikte calisirsa /joint_states topigine iki
kaynak yazar, robot_state_publisher ikisini karisik alir ve TF agaci gercek
tekerlek donusunu gostermez. Bu hata olcum sirasinda /joint_states hizinin
100 Hz yerine 121 Hz gorunmesiyle ortaya cikti. joint_state_publisher yalnizca
marco_description/display.launch.py icinde, modeli elle kurcalamak icin
kullanilir.

Ornekler:
  ros2 launch marco_bringup robot.launch.py sahte:=true
  ros2 launch marco_bringup robot.launch.py sahte:=true lidar:=true
  ros2 launch marco_bringup robot.launch.py sahte:=true rviz:=true
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
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _uyari(baglam, *args, **kwargs):
    """lidar ve rviz birlikte verilirse uyarir.

    Orange Pi'de RViz uc cekirdekten fazla CPU tuketiyor ve LiDAR surucusunu
    acliga sokuyor. Olculdu: /scan 9.96 Hz'den 4.3 Hz'e duser, 3.3 saniyelik
    bosluklar olusur, surucu "Timeout count" ve "Failed to get scan" hatalari
    basar. Hata mesajlari LiDAR'i isaret ettigi icin insan yanlis yere bakiyor,
    bu yuzden uyari burada veriliyor.
    """
    lidar = LaunchConfiguration("lidar").perform(baglam).lower() in ("true", "1")
    rviz = LaunchConfiguration("rviz").perform(baglam).lower() in ("true", "1")
    if not (lidar and rviz):
        return []
    return [
        LogInfo(msg="=" * 72),
        LogInfo(msg="UYARI: lidar ve rviz AYNI ANDA acik."),
        LogInfo(msg="RViz bu kartta ~%300 CPU aliyor ve LiDAR surucusunu acliga"),
        LogInfo(msg="sokuyor. Beklenen sonuc: /scan 10 Hz yerine ~4 Hz, arada"),
        LogInfo(msg="3 saniyelik bosluklar, 'Timeout count' ve 'Failed to get"),
        LogInfo(msg="scan' hatalari. Hata LiDAR'da DEGIL, CPU'da."),
        LogInfo(msg=""),
        LogInfo(msg="Arac hareket edecekse RViz'i kapatin ve kayit alin:"),
        LogInfo(msg="  ros2 bag record -o ~/kayit1 /scan /odom /joint_states \\"),
        LogInfo(msg="      /tf /tf_static /robot_description"),
        LogInfo(msg="  ros2 launch marco_bringup viewer.launch.py sim:=true"),
        LogInfo(msg="  ros2 bag play ~/kayit1 --clock --loop"),
        LogInfo(msg="=" * 72),
    ]


def generate_launch_description() -> LaunchDescription:
    description_share = get_package_share_directory("marco_description")
    base_share = get_package_share_directory("marco_base")
    bringup_share = get_package_share_directory("marco_bringup")
    localization_share = get_package_share_directory("marco_localization")

    xacro_file = os.path.join(description_share, "urdf", "marco.urdf.xacro")
    rviz_config = os.path.join(bringup_share, "config", "robot.rviz")
    lidar_config = os.path.join(localization_share, "config", "lidar_tmini_pro.yaml")
    lidar_filter_config = os.path.join(
        localization_share, "config", "lidar_speckle_filter.yaml"
    )

    arguments = [
        DeclareLaunchArgument("sahte", default_value="false"),
        DeclareLaunchArgument("rviz", default_value="false"),
        DeclareLaunchArgument(
            "lidar",
            default_value="false",
            description="YDLidar Tmini Pro surucusunu baslatir",
        ),
        DeclareLaunchArgument(
            "tf",
            default_value="true",
            description=(
                "odom -> base_footprint donusumunu base_driver yayinlasin. "
                "EKF devreye girdiginde false yapilmali."
            ),
        ),
        DeclareLaunchArgument(
            "serial_port",
            default_value="/dev/marco_stm32",
            description="STM32 seri port yolu",
        ),
        DeclareLaunchArgument(
            "lidar_port",
            default_value="/dev/ttyUSB0",
            description="YDLidar seri port yolu",
        ),
        DeclareLaunchArgument("fake_slip_factor", default_value="0.0"),
        DeclareLaunchArgument("fake_wheel_scale_error_left", default_value="0.0"),
        DeclareLaunchArgument("fake_wheel_scale_error_right", default_value="0.0"),
        DeclareLaunchArgument("fake_wheel_separation_actual", default_value="0.0"),
    ]

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            {
                # URDF metni tirnaksiz verilirse launch onu YAML sanip
                # ayristirmaya calisir ve hata verir; acikca str olarak
                # isaretlenmesi gerekir.
                "robot_description": ParameterValue(
                    Command(["xacro ", xacro_file]), value_type=str
                ),
                "publish_frequency": 50.0,
            }
        ],
    )

    base_driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(base_share, "launch", "base_driver.launch.py")
        ),
        launch_arguments={
            "sahte": LaunchConfiguration("sahte"),
            "tf": LaunchConfiguration("tf"),
            "port": LaunchConfiguration("serial_port"),
            "fake_slip_factor": LaunchConfiguration("fake_slip_factor"),
            "fake_wheel_scale_error_left": LaunchConfiguration(
                "fake_wheel_scale_error_left"
            ),
            "fake_wheel_scale_error_right": LaunchConfiguration(
                "fake_wheel_scale_error_right"
            ),
            "fake_wheel_separation_actual": LaunchConfiguration(
                "fake_wheel_separation_actual"
            ),
        }.items(),
    )

    # YDLidar Tmini Pro. frame_id lidar_tmini_pro.yaml'da "laser_link"
    # olarak ayarlanmis — URDF ile eslesir, ekstra static TF gerekmez.
    # ONEMLI: Node adi degistirilmemeli. YAML parametreler dugum adiyla
    # eslenir; farkli isim verilirse SDK kendi varsayilanini (/dev/ydlidar)
    # kullanir ve baglanamazken hata verir.
    lidar_node = Node(
        package="ydlidar_ros2_driver",
        executable="ydlidar_ros2_driver_node",
        name="ydlidar_ros2_driver_node",
        output="screen",
        parameters=[lidar_config, {"port": LaunchConfiguration("lidar_port")}],
        remappings=[("scan", "/scan_raw")],
        condition=IfCondition(LaunchConfiguration("lidar")),
    )

    # Hafif speckle filtresi: SLAM/AMCL/Nav2 /scan'i kullanir. Guvenlik
    # katmani gercek sistemde /scan_raw'i dinleyerek ince engelleri korur.
    lidar_filter = Node(
        package="laser_filters",
        executable="scan_to_scan_filter_chain",
        name="scan_to_scan_filter_chain",
        output="screen",
        parameters=[lidar_filter_config],
        remappings=[("scan", "/scan_raw"), ("scan_filtered", "/scan")],
        condition=IfCondition(LaunchConfiguration("lidar")),
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
            robot_state_publisher,
            base_driver,
            lidar_node,
            lidar_filter,
            rviz,
        ]
    )
