"""nav2_*_params.yaml + rpp_base + rpp_override_* birleştiricisi.

Tek kaynak: config/rpp_base.yaml
Farklar:     config/rpp_override_{real,sim}.yaml
"""

from __future__ import annotations

import copy
import os
from typing import Any

import yaml


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """override anahtarlarını base üzerine yazar; iç içe dict'leri birleştirir."""
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def _load_yaml(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"YAML kok sozlugu degil: {path}")
    return data


def load_rpp_profile(config_dir: str, profile: str) -> dict[str, Any]:
    """profile: 'real' | 'sim' → {FollowPath: {...}, velocity_smoother: {...}}."""
    if profile not in ("real", "sim"):
        raise ValueError("profile 'real' veya 'sim' olmali")
    base = _load_yaml(os.path.join(config_dir, "rpp_base.yaml"))
    override = _load_yaml(os.path.join(config_dir, f"rpp_override_{profile}.yaml"))
    return deep_merge(base, override)


def apply_rpp_to_nav2(params: dict[str, Any], rpp: dict[str, Any]) -> dict[str, Any]:
    """controller_server FollowPath ve velocity_smoother alanlarini yazar."""
    out = copy.deepcopy(params)
    follow = rpp.get("FollowPath")
    if not isinstance(follow, dict) or "plugin" not in follow:
        raise RuntimeError("RPP profilinde FollowPath.plugin yok")

    controller = out.setdefault("controller_server", {}).setdefault(
        "ros__parameters", {}
    )
    controller["FollowPath"] = copy.deepcopy(follow)

    smoother_patch = rpp.get("velocity_smoother")
    if isinstance(smoother_patch, dict):
        smoother = out.setdefault("velocity_smoother", {}).setdefault(
            "ros__parameters", {}
        )
        smoother.update(copy.deepcopy(smoother_patch))
    return out


def compose_nav2_params_file(
    *,
    nav_share: str,
    profile: str,
    params_src: str,
    params_dst: str,
    text_replacements: list[tuple[str, str]] | None = None,
) -> str:
    """Kaynak nav2 yaml'ini oku, RPP uygula, BT vs. metin degistir, yaz."""
    config_dir = os.path.join(nav_share, "config")
    with open(params_src, encoding="utf-8") as handle:
        text = handle.read()
    for old, new in text_replacements or ():
        if old not in text:
            raise RuntimeError(f"Nav2 params icinde beklenen metin yok: {old!r}")
        text = text.replace(old, new)

    params = yaml.safe_load(text)
    if not isinstance(params, dict):
        raise RuntimeError(f"Nav2 params kok sozlugu degil: {params_src}")

    rpp = load_rpp_profile(config_dir, profile)
    params = apply_rpp_to_nav2(params, rpp)

    os.makedirs(os.path.dirname(params_dst) or ".", exist_ok=True)
    with open(params_dst, "w", encoding="utf-8") as handle:
        yaml.safe_dump(
            params,
            handle,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
    return params_dst


def _cli() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nav-share", required=True)
    parser.add_argument("--profile", choices=("real", "sim"), required=True)
    parser.add_argument("--params-src", required=True)
    parser.add_argument("--params-dst", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = compose_nav2_params_file(
        nav_share=args.nav_share,
        profile=args.profile,
        params_src=args.params_src,
        params_dst=args.params_dst,
    )
    data = _load_yaml(path)
    follow = data["controller_server"]["ros__parameters"]["FollowPath"]
    print(f"wrote {path}")
    print(
        "FollowPath "
        f"v={follow['desired_linear_vel']} "
        f"lookahead={follow['lookahead_dist']} "
        f"collision_t={follow['max_allowed_time_to_collision_up_to_carrot']} "
        f"reverse={follow['allow_reversing']}"
    )
    if args.check:
        assert follow["primary_controller"].endswith("RegulatedPurePursuitController")
        assert follow["use_rotate_to_heading"] is False
        assert follow["allow_reversing"] is True
        print("check ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
