"""Faz 11 tek gercek-sistem giris noktasi.

Gercek mod varsayilandir. Herhangi bir ROS dugumu baslamadan once paketler,
harita, rota grafi ve seri cihazlar denetlenir. Sahte mod donanim cihazlarini
acmaz; yalniz o modda perception/PLC/lift test dugumleri etkinlesir.
"""

import json
import os
import stat
from pathlib import Path

import yaml
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
from launch_ros.actions import Node


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


def _check_map(map_yaml):
    image_value = None
    with open(map_yaml, encoding="utf-8") as stream:
        for line in stream:
            key, separator, value = line.partition(":")
            if separator and key.strip() == "image":
                image_value = value.strip().strip("'\"")
                break
    if not image_value:
        raise RuntimeError(f"Harita YAML dosyasinda 'image' alani yok: {map_yaml}")
    image_path = image_value
    if not os.path.isabs(image_path):
        image_path = os.path.join(os.path.dirname(map_yaml), image_path)
    if not os.path.isfile(image_path):
        raise RuntimeError(f"Harita goruntusu bulunamadi: {os.path.abspath(image_path)}")


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


def _check_device(path, label):
    if not os.path.exists(path):
        raise RuntimeError(f"{label} cihazi bulunamadi: {path}")
    mode = os.stat(path).st_mode
    if not stat.S_ISCHR(mode):
        raise RuntimeError(f"{label} yolu karakter cihazi degil: {path}")
    if not os.access(path, os.R_OK | os.W_OK):
        raise RuntimeError(
            f"{label} cihazina okuma/yazma izni yok: {path}. "
            "Kullanicinin dialout grubunu ve udev kurallarini denetleyin."
        )


def _active_field_resources(data_root):
    from marco_route.field_store import FieldStore, StoreError
    from marco_route.validator import validate_field

    store = FieldStore(data_root)
    try:
        active = store.read_active()
        if not active:
            raise RuntimeError(
                "Etkin saha yok. GUI'den sahayi dogrulayip etkinlestirin."
            )
        field_name = str(active.get("field_name", ""))
        field_dir = store.field_directory(field_name)
        current_hash = store.package_hash(field_name)
        if current_hash != active.get("package_hash"):
            raise RuntimeError(
                "Etkin saha diskte degismis; paket hash'i uyusmuyor. "
                "Yeniden dogrulayin ve etkinlestirin."
            )
        graph = store.load_graph(field_name)
        validation = validate_field(store, graph, competition_profile=True)
        if not validation.valid:
            raise RuntimeError(
                "Etkin saha production dogrulamasindan gecemedi: "
                + "; ".join(validation.errors)
            )
    except StoreError as error:
        raise RuntimeError(f"Etkin saha paketi gecersiz: {error}") from error

    manifest_path = field_dir / "field.yaml"
    try:
        with manifest_path.open("r", encoding="utf-8") as stream:
            manifest = yaml.safe_load(stream) or {}
    except (OSError, yaml.YAMLError) as error:
        raise RuntimeError(f"field.yaml okunamadi: {error}") from error
    if manifest.get("profile") != "competition":
        raise RuntimeError(
            "Production modu yalniz profile: competition saha paketini kabul eder."
        )
    map_file = field_dir / "map.yaml"
    graph_file = field_dir / "route.geojson"
    if Path(active.get("map_yaml", "")).resolve() != map_file.resolve():
        raise RuntimeError("Etkin saha map_yaml isaretcisi paketle uyusmuyor.")
    if Path(active.get("graph_file", "")).resolve() != graph_file.resolve():
        raise RuntimeError("Etkin saha graph_file isaretcisi paketle uyusmuyor.")
    _check_map(str(map_file))
    _check_graph(str(graph_file))
    return field_name, str(map_file), str(graph_file), current_hash


def _setup(context, *args, **kwargs):
    fake = _bool(context, "sahte")
    rviz_enabled = _bool(context, "rviz")
    imu_enabled = _bool(context, "imu")

    required = {
        "lane_tracking",
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
    if rviz_enabled:
        required.add("rviz2")

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

    nav_share = get_package_share_directory("marco_navigation")
    data_root = os.path.expanduser(
        LaunchConfiguration("data_root").perform(context)
    )
    if fake:
        field_name = "test"
        map_file = _resource(
            LaunchConfiguration("harita").perform(context),
            os.path.join(nav_share, "maps"), ".yaml", "Harita",
        )
        graph_file = _resource(
            LaunchConfiguration("graf").perform(context),
            os.path.join(nav_share, "graphs"), ".geojson", "Rota grafi",
        )
        field_hash = ""
        _check_map(map_file)
        _check_graph(graph_file)
    else:
        field_name, map_file, graph_file, field_hash = (
            _active_field_resources(data_root)
        )

    port_text = LaunchConfiguration("rosbridge_port").perform(context)
    try:
        rosbridge_port = int(port_text)
    except ValueError as error:
        raise RuntimeError(f"rosbridge_port tam sayi olmali: {port_text!r}") from error
    if not 1 <= rosbridge_port <= 65535:
        raise RuntimeError(f"rosbridge_port 1..65535 araliginda olmali: {rosbridge_port}")

    for name in ("x", "y", "yaw"):
        value = LaunchConfiguration(name).perform(context)
        try:
            float(value)
        except ValueError as error:
            raise RuntimeError(f"{name} sayisal olmali: {value!r}") from error

    serial_port = LaunchConfiguration("serial_port").perform(context)
    lidar_port = LaunchConfiguration("lidar_port").perform(context)
    if not fake:
        _check_device(serial_port, "STM32")
        _check_device(lidar_port, "RPLIDAR A2M12")

    navigation_share = get_package_share_directory("marco_navigation")
    docking_share = get_package_share_directory("marco_docking")
    mission_share = get_package_share_directory("marco_mission")
    bringup_share = get_package_share_directory("marco_bringup")
    lane_share = get_package_share_directory("lane_tracking")

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

    route_safe = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(navigation_share, "launch", "route_safe.launch.py")
        ),
        launch_arguments={
            "sahte": "true" if fake else "false",
            "lidar": "false" if fake else "true",
            "imu": "true" if imu_enabled else "false",
            "serial_port": serial_port,
            "lidar_port": lidar_port,
            "harita": map_file,
            "graf": graph_file,
            "baslangic": "true",
            "x": LaunchConfiguration("x"),
            "y": LaunchConfiguration("y"),
            "yaw": LaunchConfiguration("yaw"),
            "rviz": "true" if rviz_enabled else "false",
            "safety_scan_topic": "/scan",
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
        }.items(),
    )
    rosbridge = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, "launch", "gui_bridge.launch.py")
        ),
        launch_arguments={"port": str(rosbridge_port)}.items(),
    )
    route_editor = Node(
        package="marco_route",
        executable="route_editor",
        name="route_editor",
        output="screen",
        parameters=[{
            "data_root": data_root,
            "competition_profile": True,
        }],
    )

    mode = "SAHTE (motor ve seri cihazlar kapali)" if fake else "GERCEK DONANIM"
    return [
        LogInfo(msg=f"Faz 11 mod: {mode}"),
        LogInfo(msg=f"Saha: {field_name} ({field_hash or 'test'})"),
        LogInfo(msg=f"Harita: {map_file}"),
        LogInfo(msg=f"Rota grafi: {graph_file}"),
        LogInfo(msg="Hiz zinciri: Nav2 -> /cmd_vel_raw -> collision_monitor "
                    "-> /cmd_vel_safe -> twist_mux -> /cmd_vel -> base_driver"),
        front_camera, route_editor, route_safe, docking, mission, rosbridge,
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            "sahte", default_value="false",
            description="true: motor/seri cihaz yok; yalniz test mock'lari acik",
        ),
        DeclareLaunchArgument("rviz", default_value="false"),
        DeclareLaunchArgument(
            "imu", default_value="true",
            description=(
                "Gercek sistemde STM32 IMU yaw verisini filtreli odometriye ekle"
            ),
        ),
        DeclareLaunchArgument(
            "data_root", default_value="~/marco_data/fields",
            description="Etkin saha paketlerinin kok dizini",
        ),
        DeclareLaunchArgument("harita", default_value="nav_test"),
        DeclareLaunchArgument("graf", default_value="phase10_route.geojson"),
        DeclareLaunchArgument("serial_port", default_value="/dev/marco_stm32"),
        DeclareLaunchArgument("lidar_port", default_value="/dev/marco_lidar"),
        DeclareLaunchArgument("x", default_value="0.0"),
        DeclareLaunchArgument("y", default_value="0.0"),
        DeclareLaunchArgument("yaw", default_value="0.0",
                              description="Baslangic yonu, radyan"),
        DeclareLaunchArgument("rosbridge_port", default_value="9090"),
        DeclareLaunchArgument(
            "camera", default_value="/dev/marco_front_camera"
        ),
        DeclareLaunchArgument("camera_web_stream", default_value="true"),
        DeclareLaunchArgument("camera_web_port", default_value="8080"),
        OpaqueFunction(function=_setup),
    ])
