#!/usr/bin/env python3
"""Strict simulator-only Nav2 Route GeoJSON and CAD-footprint validator."""
import argparse
import json
import math
import os
import sys
from collections import defaultdict, deque

FOOTPRINT = ((0.50, 0.35), (0.50, -0.35), (-1.18, -0.35), (-1.18, 0.35))


def fail(message):
    raise ValueError(message)


def points(feature):
    geom = feature.get('geometry', {})
    if geom.get('type') == 'Point':
        return [geom.get('coordinates')]
    if geom.get('type') == 'MultiLineString':
        lines = geom.get('coordinates', [])
        return [p for line in lines for p in line]
    fail('unsupported geometry type')


def load_pgm(path):
    with open(path, 'rb') as stream:
        if stream.readline().strip() != b'P5': fail('map must be binary PGM')
        line = stream.readline()
        while line.startswith(b'#'): line = stream.readline()
        width, height = map(int, line.split())
        maximum = int(stream.readline())
        data = stream.read()
    if maximum != 255 or len(data) != width * height: fail('invalid PGM')
    return width, height, data


def validate(graph_path, map_yaml=None):
    with open(graph_path, encoding='utf-8') as stream:
        graph = json.load(stream)
    if graph.get('type') != 'FeatureCollection' or not isinstance(graph.get('features'), list):
        fail('root must be a FeatureCollection')
    nodes, edges, all_ids = {}, [], set()
    for feature in graph['features']:
        prop = feature.get('properties')
        if feature.get('type') != 'Feature' or not isinstance(prop, dict): fail('invalid feature')
        ident = prop.get('id')
        if not isinstance(ident, int) or not 0 <= ident <= 65535 or ident in all_ids: fail('duplicate/invalid id')
        all_ids.add(ident)
        coords = points(feature)
        if not coords or any(not isinstance(p, list) or len(p) < 2 or
                             not all(isinstance(v, (int, float)) and math.isfinite(v) for v in p[:2]) for p in coords):
            fail('non-finite/invalid coordinates')
        if feature['geometry']['type'] == 'Point':
            if prop.get('frame') != 'map': fail('node frame must be map')
            nodes[ident] = tuple(coords[0][:2])
        else:
            edges.append((ident, prop, coords))
    adjacency = defaultdict(list)
    for ident, prop, coords in edges:
        start, end = prop.get('startid'), prop.get('endid')
        if start not in nodes or end not in nodes: fail('edge endpoint id missing')
        if math.dist(coords[0][:2], nodes[start]) > 1e-6 or math.dist(coords[-1][:2], nodes[end]) > 1e-6:
            fail('edge geometry does not match nodes')
        metadata = prop.get('metadata')
        if not isinstance(metadata, dict): fail('edge metadata missing')
        speed = metadata.get('abs_speed_limit')
        if not isinstance(speed, (int, float)) or isinstance(speed, bool) or not math.isfinite(speed) or not 0.05 <= speed <= 0.50:
            fail('invalid abs_speed_limit')
        if 'reverse' in metadata and not isinstance(metadata['reverse'], bool): fail('reverse must be boolean')
        if 'disableable' in metadata and not isinstance(metadata['disableable'], bool): fail('disableable must be boolean')
        adjacency[start].append(end)
    if not nodes or not edges: fail('empty graph')
    unreachable = []
    for source in nodes:
        seen, todo = {source}, deque([source])
        while todo:
            for target in adjacency[todo.popleft()]:
                if target not in seen: seen.add(target); todo.append(target)
        if len(seen) != len(nodes): unreachable.append(source)
    if unreachable: fail('directed graph has unreachable nodes from: %s' % unreachable)

    if map_yaml:
        # The packaged test map has fixed, deliberately explicit map metadata.
        values = {}
        with open(map_yaml, encoding='utf-8') as stream:
            for line in stream:
                if ':' in line: values[line.split(':', 1)[0].strip()] = line.split(':', 1)[1].strip()
        resolution = float(values['resolution'])
        origin = json.loads(values['origin'])
        image = values['image']
        if not os.path.isabs(image): image = os.path.join(os.path.dirname(map_yaml), image)
        width, height, pixels = load_pgm(image)
        for ident, _prop, coords in edges:
            for a, b in zip(coords, coords[1:]):
                length = math.dist(a[:2], b[:2]); yaw = math.atan2(b[1]-a[1], b[0]-a[0])
                for i in range(max(1, math.ceil(length / (resolution * 0.5))) + 1):
                    t = min(1.0, i / max(1, math.ceil(length / (resolution * 0.5))))
                    x, y = a[0] + t*(b[0]-a[0]), a[1] + t*(b[1]-a[1])
                    # Dense samples inside the CAD rectangle catch occupied, unknown and map exterior.
                    for fx in [j / 20.0 for j in range(-24, 11)]:
                        for fy in [j / 20.0 for j in range(-7, 8)]:
                            wx = x + fx*math.cos(yaw) - fy*math.sin(yaw)
                            wy = y + fx*math.sin(yaw) + fy*math.cos(yaw)
                            px, py = int((wx-origin[0])/resolution), int((wy-origin[1])/resolution)
                            if px < 0 or py < 0 or px >= width or py >= height: fail('edge %d leaves map' % ident)
                            value = pixels[(height-1-py)*width+px]
                            if value < 250: fail('edge %d CAD sweep intersects occupied/unknown map' % ident)
    return {'nodes': len(nodes), 'edges': len(edges), 'ids': len(all_ids)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('graph'); parser.add_argument('--map')
    parser.add_argument('--result')
    args = parser.parse_args()
    try:
        summary = validate(args.graph, args.map); result = {'passed': True, **summary}
        print('PASS graph validator: %(nodes)d nodes, %(edges)d directed edges' % summary)
    except Exception as exc:
        result = {'passed': False, 'error': str(exc)}; print('FAIL graph validator: %s' % exc, file=sys.stderr)
    if args.result:
        os.makedirs(os.path.dirname(args.result), exist_ok=True)
        with open(args.result, 'w', encoding='utf-8') as stream: json.dump(result, stream, indent=2)
    return 0 if result['passed'] else 2


if __name__ == '__main__': sys.exit(main())
