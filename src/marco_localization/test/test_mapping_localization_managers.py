"""Harita artefaktlari ve yonetici karsilikli dislama testleri."""

import importlib.util
import json
import math
from pathlib import Path
from types import SimpleNamespace

import yaml
from geometry_msgs.msg import PoseWithCovarianceStamped
from marco_msgs.msg import LocalizationStatus, MappingStatus
from nav_msgs.msg import OccupancyGrid
from slam_toolbox.srv import SerializePoseGraph


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load_script(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mapping = _load_script("mapping_manager")
localization = _load_script("localization_manager")


class _RunningProcess:
    def poll(self):
        return None


class _Publisher:
    def publish(self, _message):
        pass


def _sample_map():
    message = OccupancyGrid()
    message.header.frame_id = "map"
    message.info.width = 3
    message.info.height = 2
    message.info.resolution = 0.05
    message.info.origin.position.x = -1.25
    message.info.origin.position.y = 2.5
    message.info.origin.orientation.z = math.sin(0.15)
    message.info.origin.orientation.w = math.cos(0.15)
    message.data = [-1, 0, 100, 25, 65, 50]
    return message


def _sample_pose():
    message = PoseWithCovarianceStamped()
    message.header.frame_id = "map"
    message.header.stamp.sec = 123
    message.header.stamp.nanosec = 456
    message.pose.pose.position.x = 1.2
    message.pose.pose.position.y = -0.4
    message.pose.pose.orientation.z = math.sin(0.35)
    message.pose.pose.orientation.w = math.cos(0.35)
    message.pose.covariance[0] = 0.04
    message.pose.covariance[7] = 0.04
    message.pose.covariance[35] = 0.09
    return message


def test_save_builds_complete_field_atomically(tmp_path):
    manager = SimpleNamespace(
        _state=MappingStatus.STATE_MAPPING,
        _process=_RunningProcess(),
        _latest_map=_sample_map(),
        _latest_pose=_sample_pose(),
        _field_name="test_field",
        _serialize_client=None,
        _manual_cmd_pub=_Publisher(),
        _data_root=lambda: tmp_path,
        _publish_status=lambda _message: None,
        _terminate_process=lambda: True,
    )
    manager._write_yaml = mapping.MappingManager._write_yaml
    manager._write_metadata = lambda staging, map_msg, pose_msg: (
        mapping.MappingManager._write_metadata(manager, staging, map_msg, pose_msg)
    )

    def save_graph(_client, request, _label):
        stem = Path(request.filename)
        stem.with_suffix(".posegraph").write_bytes(b"posegraph")
        stem.with_suffix(".data").write_bytes(b"data")
        return SimpleNamespace(
            result=SerializePoseGraph.Response.RESULT_SUCCESS
        )

    manager._call_service = save_graph
    response = SimpleNamespace(
        success=False, message="", field_directory="", map_yaml=""
    )

    mapping.MappingManager._on_save(manager, None, response)

    target = tmp_path / "test_field"
    assert response.success
    assert manager._state == MappingStatus.STATE_SAVED
    assert sorted(path.name for path in target.iterdir()) == [
        "calibration_snapshot.yaml",
        "field.yaml",
        "map.data",
        "map.pgm",
        "map.png",
        "map.posegraph",
        "map.yaml",
        "mapping_pose.yaml",
        "route.geojson",
        "stations.yaml",
    ]
    assert not list(tmp_path.glob(".test_field.saving-*"))

    map_yaml = yaml.safe_load((target / "map.yaml").read_text())
    assert map_yaml["image"] == "map.pgm"
    assert map_yaml["resolution"] == 0.05
    assert map_yaml["origin"] == [-1.25, 2.5, 0.3]
    pose_yaml = yaml.safe_load((target / "mapping_pose.yaml").read_text())
    assert pose_yaml["frame_id"] == "map"
    assert pose_yaml["child_frame_id"] == "base_footprint"
    assert math.isclose(pose_yaml["yaw"], 0.7)
    field_yaml = yaml.safe_load((target / "field.yaml").read_text())
    assert field_yaml["profile"] == "competition"
    assert field_yaml["route"] == "route.geojson"
    route = json.loads((target / "route.geojson").read_text())
    assert route["marco"]["schema"] == "marco.field_route"
    assert route["marco"]["version"] == 2
    stations = yaml.safe_load((target / "stations.yaml").read_text())
    assert stations == {
        "version": 1,
        "field_name": "test_field",
        "nodes": [],
    }
    assert set(field_yaml["files"]) == {
        "map.yaml",
        "map.pgm",
        "map.png",
        "map.posegraph",
        "map.data",
        "mapping_pose.yaml",
        "route.geojson",
        "stations.yaml",
        "calibration_snapshot.yaml",
    }


def test_saved_field_is_accepted_for_localization(tmp_path):
    field = tmp_path / "field_1"
    field.mkdir()
    (field / "map.pgm").write_bytes(b"P5\n1 1\n255\n\xfe")
    (field / "map.yaml").write_text(
        "image: map.pgm\nresolution: 0.05\norigin: [0.0, 0.0, 0.0]\n",
        encoding="utf-8",
    )
    (field / "mapping_pose.yaml").write_text(
        "frame_id: map\nchild_frame_id: base_footprint\n"
        "position: {x: 1.0, y: 2.0}\nyaw: 0.5\n",
        encoding="utf-8",
    )
    manager = SimpleNamespace(_data_root=lambda: tmp_path)

    validated = localization.LocalizationManager._validate_map(manager, "field_1")
    pose = localization.LocalizationManager._load_saved_pose(field)

    assert validated == (field / "map.yaml").resolve()
    assert pose == (1.0, 2.0, 0.5)


def test_failed_posegraph_save_never_exposes_partial_field(tmp_path):
    manager = SimpleNamespace(
        _state=MappingStatus.STATE_MAPPING,
        _process=_RunningProcess(),
        _latest_map=_sample_map(),
        _latest_pose=_sample_pose(),
        _field_name="failed_field",
        _serialize_client=None,
        _manual_cmd_pub=_Publisher(),
        _data_root=lambda: tmp_path,
        _publish_status=lambda _message: None,
        _call_service=lambda *_args: SimpleNamespace(result=255),
        get_logger=lambda: SimpleNamespace(error=lambda _message: None),
    )
    manager._write_yaml = mapping.MappingManager._write_yaml
    response = SimpleNamespace(
        success=False, message="", field_directory="", map_yaml=""
    )

    mapping.MappingManager._on_save(manager, None, response)

    assert response.success is False
    assert manager._state == MappingStatus.STATE_MAPPING
    assert not (tmp_path / "failed_field").exists()
    assert len(list(tmp_path.glob(".failed_field.saving-*"))) == 1


def test_mapping_rejects_active_localization():
    manager = SimpleNamespace(
        _process=None,
        _localization_state=LocalizationStatus.STATE_LOCALIZING,
        _amcl_is_running=lambda: False,
    )
    request = SimpleNamespace(field_name="field_1")
    response = SimpleNamespace(accepted=None, message="")

    mapping.MappingManager._on_start(manager, request, response)

    assert response.accepted is False
    assert "Lokalizasyon calisirken" in response.message


def test_localization_rejects_active_mapping():
    manager = SimpleNamespace(
        _process=None,
        _mapping_state=MappingStatus.STATE_MAPPING,
        _slam_toolbox_is_running=lambda: False,
    )
    request = SimpleNamespace(field_name="field_1")
    response = SimpleNamespace(accepted=None, message="", map_yaml="")

    localization.LocalizationManager._on_start(manager, request, response)

    assert response.accepted is False
    assert "Haritalama calisirken" in response.message
