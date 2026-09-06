"""Production Nav2 route runtime for one already-localized active field.

This launch deliberately contains no map server, AMCL, robot hardware,
safety supervisor, collision monitor or twist_mux.  Those remain owned by the
localization/control-plane flow.  The canonical field route.geojson is passed
unchanged to both Route Server and Route Guard.
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


def _rpp_compose():
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "rpp_compose.py")
    spec = importlib.util.spec_from_file_location("marco_rpp_compose", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_graph(context) -> str:
    raw = LaunchConfiguration("graf").perform(context).strip()
    if not raw or not os.path.isabs(raw):
        raise RuntimeError(
            "Production route runtime graf yolu mutlak olmali: "
            "<data_root>/<field_name>/route.geojson"
        )
    graph_file = os.path.realpath(raw)
    if os.path.basename(graph_file) != "route.geojson" or not os.path.isfile(graph_file):
        raise RuntimeError(f"Aktif saha route.geojson bulunamadi: {graph_file}")
    try:
        with open(graph_file, encoding="utf-8") as stream:
            graph = json.load(stream)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Rota grafi okunamadi: {graph_file}: {error}") from error
    if graph.get("type") != "FeatureCollection" or not graph.get("features"):
        raise RuntimeError(f"Rota grafi bos/gecersiz: {graph_file}")
    return graph_file


def _setup(context, *args, **kwargs):
    nav_share = get_package_share_directory("marco_navigation")
    nav2_share = get_package_share_directory("nav2_bringup")
    graph_file = _canonical_graph(context)
    bt_xml = os.path.join(nav_share, "behavior_trees", "navigate_route_wait.xml")

    nav_params = "/tmp/marco_nav2_route_runtime_params.yaml"
    _rpp_compose().compose_nav2_params_file(
        nav_share=nav_share,
        profile="real",
        params_src=os.path.join(nav_share, "config", "nav2_params.yaml"),
        params_dst=nav_params,
        text_replacements=[(
            'default_nav_to_pose_bt_xml: ""',
            f'default_nav_to_pose_bt_xml: "{bt_xml}"',
        )],
    )

    with open(os.path.join(nav_share, "config", "route_server.yaml"), encoding="utf-8") as stream:
        route_text = stream.read()
    route_text = route_text.replace(
        'graph_filepath: ""', f'graph_filepath: "{graph_file}"'
    )
    route_params = "/tmp/marco_route_runtime_server.yaml"
    with open(route_params, "w", encoding="utf-8") as stream:
        stream.write(route_text)

    nav2 = GroupAction(actions=[
        SetRemap(src="cmd_vel", dst="cmd_vel_nav"),
        SetRemap(src="cmd_vel_smoothed", dst="/cmd_vel_raw"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_share, "launch", "navigation_launch.py")
            ),
            launch_arguments={
                "use_sim_time": "false",
                "params_file": nav_params,
                "autostart": "true",
                "use_composition": "False",
            }.items(),
        ),
    ])

    return [
        LogInfo(msg=f"Production route runtime graph: {graph_file}"),
        nav2,
        Node(
            package="nav2_route",
            executable="route_server",
            name="route_server",
            output="screen",
            parameters=[route_params],
            remappings=[("tf", "/tf"), ("tf_static", "/tf_static")],
        ),
        Node(
            package="nav2_lifecycle_manager",
            executable="lifecycle_manager",
            name="lifecycle_manager_route",
            output="screen",
            parameters=[{
                "use_sim_time": False,
                "autostart": True,
                "node_names": ["route_server"],
            }],
        ),
        Node(
            package="marco_navigation",
            executable="speed_limit_manager.py",
            name="speed_limit_manager",
            output="screen",
        ),
        Node(
            package="marco_route",
            executable="route_guard",
            name="route_guard",
            output="screen",
            parameters=[{
                "graph_file": graph_file,
                "warning_threshold_m": 0.10,
                "slowdown_threshold_m": 0.15,
                "stop_threshold_m": 0.25,
                "slowdown_speed_mps": 0.06,
                "stop_debounce_s": 0.50,
            }],
        ),
    ]


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        DeclareLaunchArgument(
            "graf",
            default_value="",
            description="Aktif saha paketindeki mutlak route.geojson yolu",
        ),
        OpaqueFunction(function=_setup),
    ])
