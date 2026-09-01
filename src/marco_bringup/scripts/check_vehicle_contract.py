#!/usr/bin/env python3
"""Faz 0 arac parametrelerinin yanlis amacla degismesini engeller."""

import argparse
import ast
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import yaml


def _close(actual, expected, label):
    if not math.isclose(float(actual), float(expected), abs_tol=1e-9):
        raise ValueError(f'{label}: {actual} != {expected}')


def _read_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


def _xacro_values(path):
    root = ET.parse(path).getroot()
    return {
        item.attrib['name']: float(item.attrib['value'])
        for item in root.iter()
        if item.tag.endswith('property')
        and item.attrib.get('name') in {
            'wheel_radius', 'wheel_separation', 'lidar_x', 'lidar_y',
            'lidar_z'}
    }


def _footprints(path):
    data = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    found = []

    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == 'footprint':
                    parsed = (
                        ast.literal_eval(child)
                        if isinstance(child, str)
                        else child
                    )
                    found.append(parsed)
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(data)
    return found


def check(root: Path) -> None:
    contract = _read_yaml(
        root / 'src/marco_bringup/config/vehicle_contract.yaml'
    )
    drive = contract['drive']
    geometry = contract['geometry']
    base = _read_yaml(
        root / 'src/marco_base/config/base_driver.yaml'
    )['marco_base_driver']['ros__parameters']
    lane = _read_yaml(
        root / 'src/lane_tracking/config/lane_tracking.yaml'
    )['imgprocess_node']['ros__parameters']
    xacro = _xacro_values(
        root / 'src/marco_description/urdf/properties.xacro'
    )

    _close(base['wheel_radius'], drive['wheel_radius_m'], 'base wheel radius')
    _close(base['ticks_per_revolution'],
           drive['encoder_ticks_per_revolution'], 'encoder tick/tur')
    _close(base['wheel_separation'],
           drive['odometry_effective_wheel_separation_m'],
           'odometri etkin teker araligi')
    _close(lane['wheel_separation'],
           drive['odometry_effective_wheel_separation_m'],
           'serit takip teker araligi')
    _close(xacro['wheel_radius'], drive['wheel_radius_m'], 'URDF wheel radius')
    _close(
        xacro['wheel_separation'],
        drive['geometric_wheel_separation_m'],
        'URDF geometrik teker araligi',
    )
    for name, expected in zip(('lidar_x', 'lidar_y', 'lidar_z'),
                              geometry['lidar_base_link_xyz_m']):
        _close(xacro[name], expected, name)
    # base.xacro base_footprint_to_base_link icin wheel_radius kullanir.
    _close(
        xacro['wheel_radius'],
        geometry['base_link_height_m'],
        'base_link z',
    )
    _close(xacro['wheel_radius'] + xacro['lidar_z'],
           geometry['lidar_scan_height_m'], 'LiDAR yerden yukseklik')

    expected_footprint = geometry['footprint']
    for name in ('nav2_params.yaml', 'nav2_sim_params.yaml'):
        config_path = root / f'src/marco_navigation/config/{name}'
        values = _footprints(config_path)
        footprint_mismatch = any(
            value != expected_footprint for value in values
        )
        if len(values) != 2 or footprint_mismatch:
            raise ValueError(
                f'{name}: local/global footprint sozlesmeyle uyusmuyor'
            )

    collision = _read_yaml(
        root / 'src/marco_safety/config/collision_monitor.yaml'
    )['collision_monitor']['ros__parameters']
    footprint_x = [point[0] for point in expected_footprint]
    footprint_y = [point[1] for point in expected_footprint]
    required = {
        'FrontStop': (0.0, max(footprint_x), max(abs(v) for v in footprint_y)),
        'RearStop': (min(footprint_x), 0.0, max(abs(v) for v in footprint_y)),
    }
    for name, (min_x, max_x, half_width) in required.items():
        points = collision[name]['points']
        xs, ys = points[0::2], points[1::2]
        covered_width = max(abs(value) for value in ys) >= half_width
        if min(xs) > min_x or max(xs) < max_x or not covered_width:
            raise ValueError(f'{name}: arac footprintini kapsamiyor')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', default='')
    args = parser.parse_args()
    root = (
        Path(args.workspace).resolve()
        if args.workspace
        else Path.cwd().resolve()
    )
    if not (root / 'src/marco_bringup').is_dir():
        print('FAIL: workspace kokunde calistir veya --workspace ver')
        return 1
    try:
        check(root)
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as error:
        print(f'FAIL: {error}')
        return 1
    print('PASS: arac parametreleri, footprint ve LiDAR TF tutarli')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
