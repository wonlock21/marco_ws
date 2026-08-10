"""Tam kamera genisligine yayilan serit kontrol olcegi testleri."""

import pytest

from lane_tracking.imgprocess_node import (
    combine_lane_errors,
    enforce_minimum_wheel_speed,
    lane_end_confirmed,
    scale_lane_error,
)


@pytest.mark.parametrize(
    ('error', 'normalized', 'scaled', 'angular'),
    [
        (0.0, 0.0, 0.0, 0.0),
        (160.0, 0.5, 0.5, -0.025),
        (-160.0, -0.5, -0.5, 0.025),
        (320.0, 1.0, 1.0, -0.050),
        (-320.0, -1.0, -1.0, 0.050),
        (500.0, 1.0, 1.0, -0.050),
    ],
)
def test_hata_tam_kamera_genisligine_olceklenir(
        error, normalized, scaled, angular):
    actual_normalized, actual_scaled, actual_angular = scale_lane_error(
        error, half_frame_width=320, max_angular_speed=0.050,
        center_deadband_ratio=0.0)

    assert actual_normalized == pytest.approx(normalized)
    assert actual_scaled == pytest.approx(scaled)
    assert actual_angular == pytest.approx(angular)


def test_gecersiz_kamera_genisligi_guvenli_sifir_doner():
    assert scale_lane_error(100.0, 0, 0.050) == (0.0, 0.0, 0.0)


def test_merkez_olu_bolgesinde_donus_uretilmez():
    normalized, scaled, angular = scale_lane_error(
        3.0, half_frame_width=320, max_angular_speed=0.050,
        center_deadband_ratio=0.01)

    assert normalized == pytest.approx(0.009375)
    assert scaled == 0.0
    assert angular == 0.0


def test_olu_band_disinda_tepki_lineer_artiyor():
    normalized, scaled, angular = scale_lane_error(
        32.0, half_frame_width=320, max_angular_speed=0.050,
        center_deadband_ratio=0.01)

    assert normalized == pytest.approx(0.1)
    assert scaled == pytest.approx((0.1 - 0.01) / 0.99)
    assert angular == pytest.approx(-0.0045454545)


def test_donuste_yavas_teker_kalkis_esiginin_altina_dusmez():
    angular = 0.040
    separation = 0.460
    linear = enforce_minimum_wheel_speed(
        linear_speed=0.024,
        angular_speed=angular,
        wheel_separation=separation,
        minimum_wheel_speed=0.055,
    )
    half_track = separation * 0.5

    assert linear == pytest.approx(0.0642)
    assert linear - angular * half_track == pytest.approx(0.055)
    assert linear + angular * half_track == pytest.approx(0.0734)


def test_duzlukte_mevcut_hiz_degismez():
    linear = enforce_minimum_wheel_speed(
        linear_speed=0.060,
        angular_speed=0.0,
        wheel_separation=0.460,
        minimum_wheel_speed=0.055,
    )

    assert linear == pytest.approx(0.060)


def test_merkez_ve_yon_hatasi_lineer_birlesir():
    combined, angular = combine_lane_errors(
        position_error=0.20,
        heading_error=0.40,
        heading_gain=0.35,
        max_angular_speed=0.075,
    )

    assert combined == pytest.approx(0.34)
    assert angular == pytest.approx(-0.0255)


def test_birlesik_hata_kamera_kenarinda_sinirlanir():
    combined, angular = combine_lane_errors(
        position_error=0.90,
        heading_error=0.80,
        heading_gain=0.35,
        max_angular_speed=0.075,
    )

    assert combined == 1.0
    assert angular == pytest.approx(-0.075)


def test_kamera_acilisindaki_serit_yoklugu_son_sayilmaz():
    assert not lane_end_confirmed(
        seen_frames=0, missed_frames=30, minimum_seen_frames=15,
        missing_frames=6, loss_hold_frames=3)


def test_gecici_serit_kaybi_son_sayilmaz():
    assert not lane_end_confirmed(
        seen_frames=60, missed_frames=3, minimum_seen_frames=15,
        missing_frames=6, loss_hold_frames=3)


def test_yeterince_izlenen_seridin_kalici_kaybi_son_sayilir():
    assert lane_end_confirmed(
        seen_frames=60, missed_frames=9, minimum_seen_frames=15,
        missing_frames=9, loss_hold_frames=3)


def test_yalniz_serit_modunda_serit_sonu_devre_disidir():
    assert not lane_end_confirmed(
        seen_frames=200, missed_frames=200, minimum_seen_frames=15,
        missing_frames=9, loss_hold_frames=3, enabled=False)
