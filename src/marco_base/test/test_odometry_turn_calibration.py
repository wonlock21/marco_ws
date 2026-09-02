"""Fiziksel donus kalibrasyonu hesaplarinin birim testleri."""

import math

import pytest

from marco_base.odometry_turn_calibration import (
    FULL_TURN_RAD,
    calibrated_wheel_separation,
    normalize_angle,
)


def test_unwrap_pozitif_pi_sicramasini_korur():
    """Pozitif yonde +pi siniri gecilince iki dereceyi koru."""
    previous = math.radians(179.0)
    current = math.radians(-179.0)
    result = math.degrees(normalize_angle(current - previous))
    assert result == pytest.approx(2.0)


def test_unwrap_negatif_pi_sicramasini_korur():
    """Negatif yonde -pi siniri gecilince eksi iki dereceyi koru."""
    previous = math.radians(-179.0)
    current = math.radians(179.0)
    result = math.degrees(normalize_angle(current - previous))
    assert result == pytest.approx(-2.0)


def test_fazla_aci_olcen_odometri_teker_araligini_buyutur():
    """Fazla aci olcumu daha buyuk etkin teker araligi onersin."""
    proposed = calibrated_wheel_separation(0.460, math.radians(400.0))
    assert proposed == pytest.approx(0.460 * 400.0 / 360.0)


def test_eksik_aci_olcen_odometri_teker_araligini_kucultur():
    """Eksik aci olcumu daha kucuk etkin teker araligi onersin."""
    proposed = calibrated_wheel_separation(0.460, math.radians(-330.0))
    assert proposed == pytest.approx(0.460 * 330.0 / 360.0)


def test_kusursuz_tur_mevcut_degeri_korur():
    """Tam 360 derece olcumu mevcut araligi korusun."""
    result = calibrated_wheel_separation(0.460, FULL_TURN_RAD)
    assert result == pytest.approx(0.460)


@pytest.mark.parametrize(
    "current, measured, actual",
    [
        (0.0, FULL_TURN_RAD, FULL_TURN_RAD),
        (0.460, 0.0, FULL_TURN_RAD),
        (0.460, FULL_TURN_RAD, 0.0),
        (0.460, math.nan, FULL_TURN_RAD),
    ],
)
def test_gecersiz_degerler_reddedilir(current, measured, actual):
    """Sifir ve sonlu olmayan kalibrasyon girdilerini reddet."""
    with pytest.raises(ValueError):
        calibrated_wheel_separation(current, measured, actual)
