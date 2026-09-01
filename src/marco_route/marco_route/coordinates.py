"""Pure map/pixel coordinate conversion helpers."""

from __future__ import annotations

import math


def _normalize(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def pixel_to_map(
    pixel_x: float,
    pixel_y: float,
    screen_yaw: float,
    width: int,
    height: int,
    resolution: float,
    origin: tuple[float, float, float],
) -> tuple[float, float, float, bool]:
    values = (pixel_x, pixel_y, screen_yaw, resolution, *origin)
    if not all(math.isfinite(float(value)) for value in values):
        raise ValueError("coordinates and map metadata must be finite")
    if width <= 0 or height <= 0 or resolution <= 0.0:
        raise ValueError("map dimensions and resolution must be positive")
    local_x = float(pixel_x) * resolution
    local_y = (float(height - 1) - float(pixel_y)) * resolution
    origin_x, origin_y, origin_yaw = origin
    cosine, sine = math.cos(origin_yaw), math.sin(origin_yaw)
    x = origin_x + cosine * local_x - sine * local_y
    y = origin_y + sine * local_x + cosine * local_y
    yaw = _normalize(origin_yaw - float(screen_yaw))
    inside = 0.0 <= pixel_x < width and 0.0 <= pixel_y < height
    return x, y, yaw, inside


def map_to_pixel(
    x: float,
    y: float,
    yaw: float,
    width: int,
    height: int,
    resolution: float,
    origin: tuple[float, float, float],
) -> tuple[float, float, float, bool]:
    values = (x, y, yaw, resolution, *origin)
    if not all(math.isfinite(float(value)) for value in values):
        raise ValueError("coordinates and map metadata must be finite")
    if width <= 0 or height <= 0 or resolution <= 0.0:
        raise ValueError("map dimensions and resolution must be positive")
    origin_x, origin_y, origin_yaw = origin
    dx, dy = float(x) - origin_x, float(y) - origin_y
    cosine, sine = math.cos(origin_yaw), math.sin(origin_yaw)
    local_x = cosine * dx + sine * dy
    local_y = -sine * dx + cosine * dy
    pixel_x = local_x / resolution
    pixel_y = float(height - 1) - local_y / resolution
    screen_yaw = _normalize(origin_yaw - float(yaw))
    inside = 0.0 <= pixel_x < width and 0.0 <= pixel_y < height
    return pixel_x, pixel_y, screen_yaw, inside
