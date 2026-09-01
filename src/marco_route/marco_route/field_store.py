"""Safe field package persistence, hashing, activation and archival."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .graph_model import FieldGraph, GraphError
from .station_config import config_from_node


FIELD_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
GRAPH_FILE = "route.geojson"
STATIONS_FILE = "stations.yaml"
VALIDATION_FILE = "validation.json"
ACTIVE_POINTER = "active.yaml"
ARCHIVE_DIRECTORY = "_archive"


class StoreError(RuntimeError):
    """Raised for unsafe or incomplete field package operations."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json(path: Path, content: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(content, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _atomic_yaml(path: Path, content: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            yaml.safe_dump(content, stream, sort_keys=False, allow_unicode=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def stations_document(graph: FieldGraph) -> dict[str, Any]:
    """Return the deterministic station-node projection of a route graph."""
    nodes = []
    for node in sorted(graph.nodes.values(), key=lambda item: item.node_id):
        if not node.station:
            continue
        entry = {
            "node_id": node.node_id,
            "name": node.name,
            "role": node.role,
            "station_id": node.station,
            "pose": {"x": node.x, "y": node.y, "yaw": node.yaw},
            "load_rule": node.load_rule,
            "approach_mode": node.approach_mode,
        }
        station_config = config_from_node(node)
        if station_config is not None:
            entry["station_approach"] = station_config
        nodes.append(entry)
    return {
        "version": 1,
        "field_name": graph.field_name,
        "nodes": nodes,
    }


class FieldStore:
    def __init__(self, data_root: str | Path) -> None:
        self.root = Path(os.path.expanduser(str(data_root))).resolve()
        self._lock = threading.RLock()

    def field_directory(self, field_name: str, require: bool = True) -> Path:
        field_name = str(field_name).strip()
        if not FIELD_NAME_PATTERN.fullmatch(field_name):
            raise StoreError(
                "field_name must start with a letter or number and use only "
                "1-64 letters, numbers, '_' or '-'"
            )
        field_dir = (self.root / field_name).resolve()
        if field_dir.parent != self.root:
            raise StoreError("field directory escapes data_root")
        if require:
            if not field_dir.is_dir() or field_dir.is_symlink():
                raise StoreError(f"field directory not found: {field_dir}")
            map_yaml = field_dir / "map.yaml"
            if not map_yaml.is_file() or map_yaml.is_symlink():
                raise StoreError(f"field has no safe map.yaml: {field_dir}")
        return field_dir

    def graph_path(self, field_name: str) -> Path:
        return self.field_directory(field_name) / GRAPH_FILE

    def load_graph(self, field_name: str) -> FieldGraph:
        field_dir = self.field_directory(field_name)
        path = field_dir / GRAPH_FILE
        if not path.exists():
            return FieldGraph(field_name=field_name)
        if not path.is_file() or path.is_symlink() or path.resolve().parent != field_dir:
            raise StoreError("route.geojson must be a regular field-local file")
        try:
            with path.open("r", encoding="utf-8") as stream:
                content = json.load(stream)
            return FieldGraph.from_geojson(content, field_name)
        except (OSError, json.JSONDecodeError, GraphError, TypeError) as error:
            raise StoreError(f"route.geojson cannot be read: {error}") from error

    def save_graph(self, graph: FieldGraph) -> str:
        with self._lock:
            field_dir = self.field_directory(graph.field_name)
            path = field_dir / GRAPH_FILE
            if path.is_symlink():
                raise StoreError("route.geojson cannot be a symbolic link")
            try:
                _atomic_json(path, graph.to_geojson())
                _atomic_json(field_dir / STATIONS_FILE, stations_document(graph))
                self._refresh_manifest_hashes(field_dir)
            except (OSError, GraphError, TypeError, ValueError) as error:
                raise StoreError(f"route graph could not be written: {error}") from error
            return self.package_hash(graph.field_name)

    @staticmethod
    def _file_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def _refresh_manifest_hashes(self, field_dir: Path) -> None:
        manifest_path = field_dir / "field.yaml"
        if not manifest_path.is_file() or manifest_path.is_symlink():
            return
        with manifest_path.open("r", encoding="utf-8") as stream:
            manifest = yaml.safe_load(stream) or {}
        if not isinstance(manifest, dict):
            raise StoreError("field.yaml root must be an object")
        files = manifest.setdefault("files", {})
        if not isinstance(files, dict):
            raise StoreError("field.yaml files must be an object")
        for name in (GRAPH_FILE, STATIONS_FILE):
            path = field_dir / name
            files[name] = {"sha256": self._file_sha256(path)}
        _atomic_yaml(manifest_path, manifest)

    def package_issues(self, field_name: str) -> list[str]:
        """Return missing or unsafe canonical package artifacts."""
        field_dir = self.field_directory(field_name)
        config = self.map_config(field_name)
        image_value = config.get("image", "")
        image = Path(str(image_value))
        image_path = (
            image.resolve() if image.is_absolute() else (field_dir / image).resolve()
        )
        issues: list[str] = []
        if image_path.parent != field_dir:
            issues.append("map image escapes field directory")
        required = (
            field_dir / "field.yaml",
            field_dir / "map.yaml",
            image_path,
            field_dir / "mapping_pose.yaml",
            field_dir / GRAPH_FILE,
            field_dir / STATIONS_FILE,
            field_dir / "calibration_snapshot.yaml",
        )
        for path in required:
            if (
                not path.is_file()
                or path.is_symlink()
                or path.resolve().parent != field_dir
                or path.stat().st_size == 0
            ):
                issues.append(f"required package file is missing or unsafe: {path.name}")
        return issues

    def package_hash(self, field_name: str) -> str:
        field_dir = self.field_directory(field_name)
        map_config = self.map_config(field_name)
        image_value = map_config.get("image", "")
        image_path = (
            Path(image_value).resolve()
            if isinstance(image_value, str) and Path(image_value).is_absolute()
            else (field_dir / str(image_value)).resolve()
        )
        if image_path.parent != field_dir:
            raise StoreError("map image escapes field directory")
        candidates = [
            field_dir / "field.yaml",
            field_dir / "map.yaml",
            image_path,
            field_dir / "mapping_pose.yaml",
            field_dir / GRAPH_FILE,
            field_dir / STATIONS_FILE,
            field_dir / "calibration_snapshot.yaml",
        ]
        digest = hashlib.sha256()
        for path in candidates:
            if not path.is_file() or path.is_symlink():
                continue
            if path.resolve().parent != field_dir:
                raise StoreError(f"package file escapes field directory: {path}")
            relative_name = (
                "map_image" if path.resolve() == image_path
                else path.name
            )
            digest.update(relative_name.encode("utf-8"))
            digest.update(b"\0")
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            digest.update(b"\0")
        return digest.hexdigest()

    def read_stations(self, field_name: str) -> dict[str, Any]:
        field_dir = self.field_directory(field_name)
        path = field_dir / STATIONS_FILE
        if not path.is_file() or path.is_symlink():
            raise StoreError("stations.yaml is missing or unsafe")
        try:
            with path.open("r", encoding="utf-8") as stream:
                content = yaml.safe_load(stream)
        except (OSError, yaml.YAMLError) as error:
            raise StoreError(f"stations.yaml cannot be read: {error}") from error
        if not isinstance(content, dict):
            raise StoreError("stations.yaml root must be an object")
        return content

    def write_validation(
        self,
        field_name: str,
        package_hash: str,
        valid: bool,
        errors: list[str],
        warnings: list[str],
        competition_profile: bool,
    ) -> dict[str, Any]:
        with self._lock:
            if package_hash != self.package_hash(field_name):
                raise StoreError("field changed while validation report was written")
            report = {
                "version": 1,
                "field_name": field_name,
                "package_hash": package_hash,
                "valid": bool(valid),
                "errors": list(errors),
                "warnings": list(warnings),
                "competition_profile": bool(competition_profile),
                "validated_at": utc_now(),
            }
            _atomic_json(self.field_directory(field_name) / VALIDATION_FILE, report)
            return report

    def read_validation(self, field_name: str) -> dict[str, Any]:
        field_dir = self.field_directory(field_name)
        path = field_dir / VALIDATION_FILE
        if not path.is_file() or path.is_symlink():
            raise StoreError("successful validation.json report is required")
        try:
            with path.open("r", encoding="utf-8") as stream:
                report = json.load(stream)
        except (OSError, json.JSONDecodeError) as error:
            raise StoreError(f"validation.json cannot be read: {error}") from error
        if not isinstance(report, dict):
            raise StoreError("validation.json root must be an object")
        return report

    def map_config(self, field_name: str) -> dict[str, Any]:
        field_dir = self.field_directory(field_name)
        path = field_dir / "map.yaml"
        try:
            with path.open("r", encoding="utf-8") as stream:
                content = yaml.safe_load(stream) or {}
        except (OSError, yaml.YAMLError) as error:
            raise StoreError(f"map.yaml cannot be read: {error}") from error
        if not isinstance(content, dict):
            raise StoreError("map.yaml root must be an object")
        resolution = content.get("resolution")
        origin = content.get("origin")
        if (
            not isinstance(resolution, (int, float))
            or float(resolution) <= 0.0
            or not isinstance(origin, list)
            or len(origin) != 3
            or not all(isinstance(value, (int, float)) for value in origin)
        ):
            raise StoreError("map.yaml resolution/origin is invalid")
        return content

    def map_dimensions(self, field_name: str) -> tuple[int, int]:
        field_dir = self.field_directory(field_name)
        manifest = field_dir / "field.yaml"
        if manifest.is_file() and not manifest.is_symlink():
            try:
                with manifest.open("r", encoding="utf-8") as stream:
                    content = yaml.safe_load(stream) or {}
                map_data = content.get("map", {})
                width, height = int(map_data.get("width", 0)), int(
                    map_data.get("height", 0)
                )
                if width > 0 and height > 0:
                    return width, height
            except (OSError, ValueError, TypeError, yaml.YAMLError):
                pass
        config = self.map_config(field_name)
        image = (field_dir / str(config.get("image", ""))).resolve()
        if image.parent != field_dir or not image.is_file() or image.is_symlink():
            raise StoreError("map image is missing or outside field directory")
        if image.suffix.lower() != ".pgm":
            raise StoreError("map dimensions require field.yaml or a PGM map image")
        try:
            with image.open("rb") as stream:
                tokens: list[bytes] = []
                while len(tokens) < 4:
                    line = stream.readline()
                    if not line:
                        break
                    line = line.split(b"#", 1)[0]
                    tokens.extend(line.split())
            if len(tokens) < 4 or tokens[0] not in (b"P2", b"P5"):
                raise ValueError("invalid PGM header")
            width, height = int(tokens[1]), int(tokens[2])
        except (OSError, ValueError) as error:
            raise StoreError(f"map image dimensions cannot be read: {error}") from error
        if width <= 0 or height <= 0:
            raise StoreError("map image dimensions are invalid")
        return width, height

    def read_active(self) -> dict[str, Any] | None:
        path = self.root / ACTIVE_POINTER
        if not path.exists():
            return None
        if not path.is_file() or path.is_symlink():
            raise StoreError("active field pointer is unsafe")
        try:
            with path.open("r", encoding="utf-8") as stream:
                value = json.load(stream)
        except (OSError, json.JSONDecodeError) as error:
            raise StoreError(f"active field pointer cannot be read: {error}") from error
        if not isinstance(value, dict):
            raise StoreError("active field pointer is invalid")
        return value

    def activate(
        self,
        field_name: str,
        expected_hash: str = "",
        competition_profile: bool | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            field_dir = self.field_directory(field_name)
            issues = self.package_issues(field_name)
            if issues:
                raise StoreError("; ".join(issues))
            current_hash = self.package_hash(field_name)
            if expected_hash and expected_hash != current_hash:
                raise StoreError("field changed since validation; hash mismatch")
            report = self.read_validation(field_name)
            if (
                report.get("field_name") != field_name
                or report.get("package_hash") != current_hash
                or report.get("valid") is not True
                or (
                    competition_profile is not None
                    and report.get("competition_profile")
                    is not bool(competition_profile)
                )
            ):
                raise StoreError(
                    "validation.json is not a successful report for the current hash"
                )
            try:
                with (field_dir / "field.yaml").open(
                    "r", encoding="utf-8"
                ) as stream:
                    manifest = yaml.safe_load(stream) or {}
                package_version = str(manifest.get("version", ""))
            except (OSError, AttributeError, yaml.YAMLError) as error:
                raise StoreError(f"field.yaml cannot be read: {error}") from error
            value = {
                "version": 1,
                "field_name": field_name,
                "package_version": package_version,
                "package_hash": current_hash,
                "graph_file": str(field_dir / GRAPH_FILE),
                "map_yaml": str(field_dir / "map.yaml"),
                "activated_at": utc_now(),
            }
            _atomic_json(self.root / ACTIVE_POINTER, value)
            return value

    def archive(self, field_name: str) -> Path:
        with self._lock:
            field_dir = self.field_directory(field_name)
            active = self.read_active()
            if active and active.get("field_name") == field_name:
                raise StoreError("active field cannot be archived")
            archive_root = self.root / ARCHIVE_DIRECTORY
            archive_root.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            target = archive_root / f"{field_name}-{stamp}"
            try:
                os.replace(field_dir, target)
                directory_fd = os.open(self.root, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError as error:
                raise StoreError(f"field could not be archived atomically: {error}") from error
            return target
