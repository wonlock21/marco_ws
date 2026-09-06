"""Tek gercek-sistem giris noktasi.

Gercek mod varsayilandir. Kontrol katmani harita secilmeden ayaga kalkar;
kayitli saha, lokalizasyon ve demo GUI servisleriyle sonradan baslatilir.
Production gorevleri ise dogrulanmis etkin saha olmadan hareket yetkisi almaz.
"""

import json
import os

from ament_index_python.packages import (
    PackageNotFoundError,
    get_package_prefix,
    get_package_share_directory,
)
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def _bool(context, name):
    return LaunchConfiguration(name).perform(context).lower() in (
        "true", "1", "yes", "on",
    )


def _resource(value, directory, extension, label):
    candidate = value
    if not candidate.endswith(extension):
        candidate += extension
    if not os.path.isabs(candidate):
        candidate = os.path.join(directory, candidate)
    candidate = os.path.abspath(candidate)
    if not os.path.isfile(candidate):
        raise RuntimeError(f"{label} bulunamadi: {candidate}")
    return candidate


def _check_graph(graph_file):
    try:
        with open(graph_file, encoding="utf-8") as stream:
            graph = json.load(stream)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Rota grafi okunamadi: {graph_file}: {error}") from error
    if graph.get("type") != "FeatureCollection" or not graph.get("features"):
        raise RuntimeError(
            f"Rota grafi bos veya GeoJSON FeatureCollection degil: {graph_file}"
        )


def _setup(context, *args, **kwargs):
    fake = _bool(context, "sahte")
    imu_enabled = _bool(context, "imu")

    required = {
        "lane_tracking", "marco_demo",
        "marco_base", "marco_bringup", "marco_description", "marco_docking",
        "marco_localization", "marco_mission", "marco_msgs", "marco_navigation",
        "marco_route",
        "marco_safety", "nav2_amcl", "nav2_bringup", "nav2_collision_monitor",
        "nav2_map_server", "nav2_route", "robot_localization",
        "robot_state_publisher", "rosbridge_server", "twist_mux", "usb_cam",
        "web_video_server", "xacro",
    }
    if fake:
        required.add("marco_perception")
    else:
        required.add("rplidar_ros")
    if imu_enabled:
        required.add("imu_filter_madgwick")
    missing = []
    for package in sorted(required):
        try:
            get_package_prefix(package)
        except PackageNotFoundError:
            missing.append(package)
    if missing:
        raise RuntimeError(
            "Eksik ROS paketleri: " + ", ".join(missing)
            + ". Gerekli overlay'leri source edin veya paketleri kurun."
        )

    data_root = os.path.expanduser(
        LaunchConfiguration("data_root").perform(context)
    )
    nav_share = get_package_share_directory("marco_navigation")
    # Paketli test grafi yalniz sahte mod icindir. Production mission manager
    # bos baslar ve grafi sadece dogrulanmis /fields/active mesajindan alir.
    graph_file = ""
    if fake:
        graph_file = _resource(
            LaunchConfiguration("graf").perform(context),
            os.path.join(nav_share, "graphs"), ".geojson", "Test rota grafi",
        )
        _check_graph(graph_file)

    port_text = LaunchConfiguration("rosbridge_port").perform(context)
    try:
        rosbridge_port = int(port_text)
    except ValueError as error:
        raise RuntimeError(f"rosbridge_port tam sayi olmali: {port_text!r}") from error
    if not 1 <= rosbridge_port <= 65535:
        raise RuntimeError(f"rosbridge_port 1..65535 araliginda olmali: {rosbridge_port}")

    serial_port = LaunchConfiguration("serial_port").perform(context)
    lidar_port = LaunchConfiguration("lidar_port").perform(context)

    localization_share = get_package_share_directory("marco_localization")
    docking_share = get_package_share_directory("marco_docking")
    mission_share = get_package_share_directory("marco_mission")

    control_plane = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                localization_share, "launch", "mapping_control.launch.py"
            )
        ),
        launch_arguments={
            "sahte": "true" if fake else "false",
            "imu": "true" if imu_enabled else "false",
            "obstacle_detection": LaunchConfiguration("obstacle_detection"),
            "serial_port": serial_port,
            "lidar_port": lidar_port,
            "data_root": data_root,
            "camera": LaunchConfiguration("camera"),
            "camera_web_stream": LaunchConfiguration("camera_web_stream"),
            "camera_web_port": LaunchConfiguration("camera_web_port"),
            "demo_use_lane_tracking": LaunchConfiguration(
                "demo_use_lane_tracking"
            ),
            "rosbridge_port": str(rosbridge_port),
        }.items(),
    )
    docking = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(docking_share, "launch", "docking.launch.py")
        ),
        launch_arguments={
            "mock": "true" if fake else "false",
            "lane_tracking": "false" if fake else "true",
        }.items(),
    )
    mission = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(mission_share, "launch", "mission.launch.py")
        ),
        launch_arguments={
            "task_source": "mock_plc" if fake else "plc",
            "simulate_steps": "false",
            "graph_file": graph_file,
            "require_active_field": "false" if fake else "true",
            "manual_task_enabled": "true",
            "test_only_lift": "true" if fake else "false",
            "imu": "true" if imu_enabled else "false",
        }.items(),
    )
    mode = "SAHTE (motor ve seri cihazlar kapali)" if fake else "GERCEK DONANIM"
    return [
        LogInfo(msg=f"Sistem modu: {mode}"),
        LogInfo(msg="Kontrol katmani hazir; etkin saha baslangicta zorunlu degil"),
        LogInfo(msg="GUI Kayitli Haritalar secimi /localization/start ile "
                    "AMCL ve donanim katmanini baslatir"),
        LogInfo(msg="Demo Nav2, GUI'deki Demoyu Baslat eyleminde baslatilir"),
        LogInfo(msg="Production gorevi dogrulanmis etkin saha gelene kadar kilitli"),
        control_plane, docking, mission,
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            "sahte", default_value="false",
            description="true: motor/seri cihaz yok; yalniz test mock'lari acik",
        ),
        DeclareLaunchArgument(
            "imu", default_value="true",
            description=(
                "Gercek sistemde STM32 IMU yaw verisini filtreli odometriye ekle"
            ),
        ),
        DeclareLaunchArgument(
            "data_root", default_value="~/marco_data/fields",
            description="Kayitli saha paketlerinin kok dizini",
        ),
        DeclareLaunchArgument(
            "graf",
            default_value="phase10_route.geojson",
            description=(
                "Yalniz sahte mod mission grafi; production tarafinda yok sayilir"
            ),
        ),
        DeclareLaunchArgument("serial_port", default_value="/dev/marco_stm32"),
        DeclareLaunchArgument("lidar_port", default_value="/dev/marco_lidar"),
        DeclareLaunchArgument(
            "obstacle_detection", default_value="true",
            description="Gercek sistem guvenlik engel algilamasi",
        ),
        DeclareLaunchArgument(
            "demo_use_lane_tracking", default_value="false",
            description="Kayitli A/B demosunda serit takibini etkinlestir",
        ),
        DeclareLaunchArgument("rosbridge_port", default_value="9090"),
        DeclareLaunchArgument(
            "camera", default_value="/dev/marco_front_camera"
        ),
        DeclareLaunchArgument("camera_web_stream", default_value="true"),
        DeclareLaunchArgument("camera_web_port", default_value="8080"),
        OpaqueFunction(function=_setup),
    ])
