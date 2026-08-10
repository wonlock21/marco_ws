"""180 derece donus kontrol hesabinin birim testleri."""

import math
from types import SimpleNamespace

import pytest

from lane_tracking.turnaround_node import (
    angular_command,
    normalize_angle,
    quaternion_yaw,
    slew_limited_speed,
)


def test_aci_sarmasi_pi_sinirinda_kucuk_fark_uretir():
    before = math.radians(179.0)
    after = math.radians(-179.0)

    assert normalize_angle(after - before) == pytest.approx(
        math.radians(2.0))


def test_quaternion_yaw_doksan_dereceyi_bulur():
    quaternion = SimpleNamespace(
        x=0.0, y=0.0,
        z=math.sin(math.pi / 4.0),
        w=math.cos(math.pi / 4.0),
    )

    assert quaternion_yaw(quaternion) == pytest.approx(math.pi / 2.0)


def test_uzakta_maksimum_donus_hizi_sinirlanir():
    assert angular_command(
        remaining=math.pi, gain=0.8, minimum=0.08, maximum=0.30,
    ) == pytest.approx(0.30)


def test_hedefe_yakinda_minimum_donus_hizi_korunur():
    assert angular_command(
        remaining=math.radians(4.0), gain=0.8,
        minimum=0.08, maximum=0.30,
    ) == pytest.approx(0.08)


def test_donus_hizi_ani_sicrama_yapmadan_rampalanir():
    assert slew_limited_speed(
        current=0.0, target=0.27, acceleration=0.20, period=0.1,
    ) == pytest.approx(0.02)


def test_rampa_hedef_hizi_gecmez():
    assert slew_limited_speed(
        current=0.26, target=0.27, acceleration=0.20, period=0.1,
    ) == pytest.approx(0.27)


def test_yavaslama_ayri_oranla_sinirlanir():
    assert slew_limited_speed(
        current=0.24, target=0.18, acceleration=0.12, period=0.1,
        deceleration=0.18,
    ) == pytest.approx(0.222)
