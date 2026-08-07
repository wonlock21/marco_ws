"""EKF tabanli lokalizasyon katmanini baslatir.

Bu launch dosyasi:
  1. marco_bringup/robot.launch.py'yi TF KAPALIYKEN cagirarak donanim
     katmanini ayaga kaldirir.
  2. robot_localization ekf_node'u baslatir; o da odom -> base_footprint
     TF'ini yayinlar.
  3. imu:=true ise IMU filtre node'unu da baslatir.

publish_tf cakismasini onlemek icin robot.launch.py tf:=false argumaniyla
cagriliyor. Bu, joint_state_publisher entegrasyon tuzaginin yaninda karsimiza
cikan ikinci TF cakisma noktasidir: ikisi de ayni donusumu yayinlarsa TF agaci
kararli degil.

Ornekler:
  ros2 launch marco_localization localization.launch.py sahte:=true
  ros2 launch marco_localization localization.launch.py sahte:=true imu:=true
  ros2 launch marco_localization localization.launch.py sahte:=true rviz:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    """IMU argumanina gore EKF yapilandirma dosyasini sec.

    LaunchConfiguration substitution'lari bir Python degeri gibi dogrudan
    karsilastirilamiyor; .perform(context) cagrisina ihtiyac var. Bu yuzden
    OpaqueFunction kullaniyoruz.
    """
    imu_enabled = LaunchConfiguration("imu").perform(context).lower() in ("true", "1", "yes")

    localization_share = get_package_share_directory("marco_localization")
    bringup_share = get_package_share_directory("marco_bringup")

    config_file = "ekf_imu.yaml" if imu_enabled else "ekf_odom.yaml"
    ekf_config = os.path.join(localization_share, "config", config_file)

    # Donanim katmani. TF kapalı: EKF odom -> base_footprint'i yayinlayacak.
    robot_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, "launch", "robot.launch.py")
        ),
        launch_arguments={
            "sahte": LaunchConfiguration("sahte"),
            "tf": "false",
            "rviz": LaunchConfiguration("rviz"),
            "lidar": LaunchConfiguration("lidar"),
            "serial_port": LaunchConfiguration("serial_port"),
            "lidar_port": LaunchConfiguration("lidar_port"),
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

    ekf_node = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node",
        output="screen",
        parameters=[ekf_config],
    )

    nodes = [robot_launch, ekf_node]

    # IMU aktifse imu_filter_madgwick'i de baslatiyoruz.
    # Bu dugum ham accel+gyro'dan quaternion orientation hesaplar ve
    # robot_localization'in beklendigi sekilde sensor_msgs/Imu yayinlar.
    # Manyetometre olmadigi icin yalnizca gyro entegrasyon modunda calistirilir
    # (use_mag: false).
    if imu_enabled:
        imu_filter = Node(
            package="imu_filter_madgwick",
            executable="imu_filter_madgwick_node",
            name="imu_filter",
            output="screen",
            parameters=[{
                "use_mag": False,
                # Gyro entegrasyonu ile elde edilen yaw orientasyonu
                # robot_localization'a gidiyor ama biz orada kullanmiyoruz
                # (imu0_config'de yaw=false). Sadece gyro yaw hizi (twist)
                # ve ivme kullaniliyor. Bu filtre yalnizca gravity removal
                # ve olasi gelecek kullanim icin buradadir.
                "publish_tf": False,
                "world_frame": "enu",
                "gain": 0.1,
                "zeta": 0.0,
                "fixed_frame": "",
                "orientation_stddev": 0.05,
                "angular_scale": 1.0,
            }],
            remappings=[
                ("imu/data_raw", "/imu/data_raw"),
                ("imu/data", "/imu/data"),
            ],
        )
        nodes.append(imu_filter)

    return nodes


def generate_launch_description() -> LaunchDescription:
    arguments = [
        DeclareLaunchArgument(
            "sahte",
            default_value="false",
            description="Gercek STM32 yerine yazilim taklidini kullan",
        ),
        DeclareLaunchArgument(
            "lidar",
            default_value="false",
            description="YDLidar Tmini Pro surucusunu baslatir",
        ),
        DeclareLaunchArgument(
            "imu",
            default_value="false",
            description=(
                "IMU girdisini EKF'e ekle. true yapildiginda imu_filter_madgwick "
                "de baslatilir ve /imu/data_raw topigi beklenilir."
            ),
        ),
        DeclareLaunchArgument(
            "rviz",
            default_value="false",
            description="RViz2 gorsellestirici",
        ),
        DeclareLaunchArgument("serial_port", default_value="/dev/marco_stm32"),
        DeclareLaunchArgument("lidar_port", default_value="/dev/ttyUSB0"),
        DeclareLaunchArgument("fake_slip_factor", default_value="0.0"),
        DeclareLaunchArgument("fake_wheel_scale_error_left", default_value="0.0"),
        DeclareLaunchArgument("fake_wheel_scale_error_right", default_value="0.0"),
        DeclareLaunchArgument("fake_wheel_separation_actual", default_value="0.0"),
    ]

    return LaunchDescription(arguments + [OpaqueFunction(function=launch_setup)])
