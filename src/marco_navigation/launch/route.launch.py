"""AMCL + Nav2 + nav2_route (Faz 7).

Zincir:
  navigation.launch.py  (AMCL + controller/planner/bt_navigator)
  + route_server        (GeoJSON rota agi)
  + lifecycle_manager_route

BT: navigate_route_wait.xml — ComputeRoute ile ilk path, ardindan
    Parallel(ComputeAndTrackRoute, FollowPath). AdjustSpeedLimit
    abs_speed_limit → /speed_limit.
    (serbest NavFn yok; engelde Wait).

Ornekler:
  # Sahte/test: bos graf → demo_rota.geojson
  ros2 launch marco_navigation route.launch.py \\
      sahte:=true lidar:=true harita:=nav_test baslangic:=true

  # Gercek mod: graf zorunlu (demo fallback YOK)
  ros2 launch marco_navigation route.launch.py \\
      sahte:=false lidar:=true harita:=nav_test \\
      graf:=gercek_saha.geojson baslangic:=true

  # Dugum ID ile rota (smoke):
  ros2 run marco_navigation rota_hesapla.py --start 0 --goal 8

Orange Pi'de rviz:=true VERME.
"""

import importlib.util
import json
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetRemap

_DEMO_GRAPH = "demo_rota.geojson"


def _rpp_compose():
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "rpp_compose.py")
    spec = importlib.util.spec_from_file_location("marco_rpp_compose", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sahte_mi(context) -> bool:
    return LaunchConfiguration("sahte").perform(context).lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def _list_graphs(graphs_dir: str) -> list[str]:
    if not os.path.isdir(graphs_dir):
        return []
    return sorted(name for name in os.listdir(graphs_dir) if name.endswith(".geojson"))


def _check_graph(graph_file: str) -> None:
    try:
        with open(graph_file, encoding="utf-8") as stream:
            graph = json.load(stream)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Rota grafi okunamadi: {graph_file}: {error}"
        ) from error
    if graph.get("type") != "FeatureCollection" or not graph.get("features"):
        raise RuntimeError(
            f"Rota grafi bos veya GeoJSON FeatureCollection degil: {graph_file}"
        )


def _resolve_graph(context, nav_share: str) -> str:
    """Gercek modda bos/eksik graf → net hata. Demo fallback yalniz sahte:=true."""
    graphs_dir = os.path.join(nav_share, "graphs")
    raw = LaunchConfiguration("graf").perform(context).strip()
    fake = _sahte_mi(context)

    if not raw:
        if not fake:
            available = ", ".join(_list_graphs(graphs_dir)) or "(yok)"
            raise RuntimeError(
                "Gercek modda rota grafi zorunlu (graf:=...). "
                "Bos graf ile demo_rota.geojson sessizce acilmaz; "
                "hareket baslamadan duruldu. "
                f"Ornek: graf:=gercek_saha.geojson | mevcut: {available}. "
                "Demo fallback yalniz sahte:=true / test modunda."
            )
        raw = _DEMO_GRAPH

    graph_file = raw
    if not graph_file.endswith(".geojson"):
        graph_file += ".geojson"
    if not os.path.isabs(graph_file):
        graph_file = os.path.join(graphs_dir, graph_file)
    graph_file = os.path.abspath(graph_file)

    if not os.path.isfile(graph_file):
        available = ", ".join(_list_graphs(graphs_dir)) or "(yok)"
        raise RuntimeError(
            f"Rota grafi bulunamadi: {graph_file}. "
            f"share/graphs altindakiler: {available}. "
            "Hareket baslamadan duruldu."
        )
    _check_graph(graph_file)
    return graph_file


def _kur(context, *args, **kwargs):
    nav_share = get_package_share_directory("marco_navigation")
    loc_share = get_package_share_directory("marco_localization")
    bringup_share = get_package_share_directory("nav2_bringup")

    params_src = os.path.join(nav_share, "config", "nav2_params.yaml")
    route_params_src = os.path.join(nav_share, "config", "route_server.yaml")
    bt_xml = os.path.join(
        nav_share, "behavior_trees", "navigate_route_wait.xml"
    )
    graph_file = _resolve_graph(context, nav_share)

    params_file = "/tmp/marco_nav2_route_params.yaml"
    _rpp_compose().compose_nav2_params_file(
        nav_share=nav_share,
        profile="real",
        params_src=params_src,
        params_dst=params_file,
        text_replacements=[
            (
                'default_nav_to_pose_bt_xml: ""',
                f'default_nav_to_pose_bt_xml: "{bt_xml}"',
            )
        ],
    )

    # graph_filepath'i mutlak yaz
    with open(route_params_src, encoding="utf-8") as f:
        route_metin = f.read()
    route_metin = route_metin.replace(
        'graph_filepath: ""',
        f'graph_filepath: "{graph_file}"',
    )
    route_params_file = "/tmp/marco_route_server.yaml"
    with open(route_params_file, "w", encoding="utf-8") as f:
        f.write(route_metin)

    amcl = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(loc_share, "launch", "amcl.launch.py")
        ),
        launch_arguments={
            "sahte": LaunchConfiguration("sahte"),
            "lidar": LaunchConfiguration("lidar"),
            "imu": LaunchConfiguration("imu"),
            "serial_port": LaunchConfiguration("serial_port"),
            "lidar_port": LaunchConfiguration("lidar_port"),
            "harita": LaunchConfiguration("harita"),
            "baslangic": LaunchConfiguration("baslangic"),
            "x": LaunchConfiguration("x"),
            "y": LaunchConfiguration("y"),
            "yaw": LaunchConfiguration("yaw"),
            "rviz": LaunchConfiguration("rviz"),
        }.items(),
    )

    # Nav2 controller/behavior cikislari once cmd_vel_nav'da toplanir. Yalniz
    # velocity_smoother cikisi nav_cmd_vel'e gider. Boylece base driver /cmd_vel'de
    # kalir ve hicbir Nav2 dugumu guvenlik zincirinin son topigine yazmaz.
    nav2 = GroupAction(
        actions=[
            SetRemap(src="cmd_vel", dst="cmd_vel_nav"),
            SetRemap(
                src="cmd_vel_smoothed", dst=LaunchConfiguration("nav_cmd_vel")
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(bringup_share, "launch", "navigation_launch.py")
                ),
                launch_arguments={
                    "use_sim_time": "false",
                    "params_file": params_file,
                    "autostart": "true",
                    "use_composition": "False",
                }.items(),
            ),
        ]
    )

    route_server = Node(
        package="nav2_route",
        executable="route_server",
        name="route_server",
        output="screen",
        parameters=[route_params_file],
        remappings=[("tf", "/tf"), ("tf_static", "/tf_static")],
    )

    lifecycle_route = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_route",
        output="screen",
        parameters=[
            {
                "use_sim_time": False,
                "autostart": True,
                "node_names": ["route_server"],
            }
        ],
    )

    return [
        LogInfo(msg=f"Route BT: {bt_xml}"),
        LogInfo(msg=f"Route graf: {graph_file}"),
        LogInfo(msg=f"Nav2 params: {params_file}"),
        amcl,
        nav2,
        route_server,
        lifecycle_route,
    ]


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument("sahte", default_value="true"),
            DeclareLaunchArgument("lidar", default_value="true"),
            DeclareLaunchArgument(
                "imu",
                default_value="false",
                description=(
                    "true ise EKF imu_imu.yaml + madgwick. "
                    "Donanim yoksa once fake_imu yayinla."
                ),
            ),
            DeclareLaunchArgument("serial_port", default_value="/dev/marco_stm32"),
            DeclareLaunchArgument("lidar_port", default_value="/dev/ttyUSB0"),
            DeclareLaunchArgument("rviz", default_value="false"),
            DeclareLaunchArgument("nav_cmd_vel", default_value="/cmd_vel"),
            DeclareLaunchArgument("harita", default_value="nav_test"),
            DeclareLaunchArgument("baslangic", default_value="true"),
            DeclareLaunchArgument("x", default_value="0.0"),
            DeclareLaunchArgument("y", default_value="0.0"),
            DeclareLaunchArgument("yaw", default_value="0.0"),
            DeclareLaunchArgument(
                "graf",
                default_value="",
                description=(
                    "GeoJSON yolu; goreli ise share/graphs/ altinda aranir. "
                    "Bos: yalniz sahte:=true iken demo_rota.geojson. "
                    "sahte:=false iken zorunlu — eksik/bos graf hata ile durur."
                ),
            ),
            OpaqueFunction(function=_kur),
        ]
    )
