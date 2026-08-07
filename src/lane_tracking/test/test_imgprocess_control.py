"""Tam kamera genisligine yayilan serit kontrol olcegi testleri."""

import pytest

from lane_tracking.imgprocess_node import scale_lane_error


@pytest.mark.parametrize(
    ('error', 'normalized', 'curved', 'angular'),
    [
        (0.0, 0.0, 0.0, 0.0),
        (160.0, 0.5, 0.25, -0.0125),
        (-160.0, -0.5, -0.25, 0.0125),
        (320.0, 1.0, 1.0, -0.050),
        (-320.0, -1.0, -1.0, 0.050),
        (500.0, 1.0, 1.0, -0.050),
    ],
)
def test_hata_tam_kamera_genisligine_olceklenir(
        error, normalized, curved, angular):
    actual_normalized, actual_curved, actual_angular = scale_lane_error(
        error, half_frame_width=320, max_angular_speed=0.050,
        steering_exponent=2.0, center_deadband_ratio=0.0)

    assert actual_normalized == pytest.approx(normalized)
    assert actual_curved == pytest.approx(curved)
    assert actual_angular == pytest.approx(angular)


def test_gecersiz_kamera_genisligi_guvenli_sifir_doner():
    assert scale_lane_error(100.0, 0, 0.050) == (0.0, 0.0, 0.0)


def test_merkez_olu_bolgesinde_donus_uretilmez():
    normalized, curved, angular = scale_lane_error(
        8.0, half_frame_width=320, max_angular_speed=0.050,
        steering_exponent=2.0, center_deadband_ratio=0.03)

    assert normalized == pytest.approx(0.025)
    assert curved == 0.0
    assert angular == 0.0
