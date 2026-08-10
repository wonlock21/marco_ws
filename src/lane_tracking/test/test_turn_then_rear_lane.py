"""Donus sonrasi arka kamera hizalama karar testleri."""

import pytest

from lane_tracking.turn_then_rear_lane_node import (
    alignment_confirmed,
    camera_steering_command,
)


def test_serit_bulunmadan_hizalama_tamamlanmaz():
    assert not alignment_confirmed(
        False, 1.0, 0.0, 0.0, 0.35, 0.05, 0.10)


def test_dusuk_guvenle_hizalama_tamamlanmaz():
    assert not alignment_confirmed(
        True, 0.20, 0.0, 0.0, 0.35, 0.05, 0.10)


def test_yanal_hata_tolerans_disindaysa_hizalama_tamamlanmaz():
    assert not alignment_confirmed(
        True, 0.80, 0.08, 0.0, 0.35, 0.05, 0.10)


def test_konum_ve_yon_toleranstaysa_hizalama_tamamlanir():
    assert alignment_confirmed(
        True, 0.80, 0.03, 0.06, 0.35, 0.05, 0.10)


def test_arka_kamera_direksiyon_isaretini_on_kameraya_gore_cevirir():
    front_command = camera_steering_command(0.5, 0.10, 1.0)
    rear_command = camera_steering_command(0.5, 0.10, -1.0)

    assert front_command == pytest.approx(-0.05)
    assert rear_command == pytest.approx(0.05)
