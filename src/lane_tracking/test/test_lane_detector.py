"""Serit algilayicinin temel davranis testleri."""

import cv2
import numpy as np
import pytest

from lane_tracking.lane_detector import LaneDetector


def test_serit_yokken_bulunamadi_doner():
    frame = np.full((240, 320, 3), 255, dtype=np.uint8)

    found, error = LaneDetector().process(frame, center_x=160)

    assert found is False
    assert error == 0.0


def test_sagdaki_siyah_serit_pozitif_hata_uretir():
    frame = np.full((240, 320, 3), 255, dtype=np.uint8)
    cv2.rectangle(frame, (210, 80), (250, 239), (0, 0, 0), -1)

    found, error = LaneDetector().process(frame, center_x=160)

    assert found is True
    assert 65.0 <= error <= 75.0


def test_isik_gradyaninda_grimsi_siyah_serit_bulunur():
    gradient = np.linspace(105, 205, 320, dtype=np.uint8)
    frame = np.repeat(gradient[np.newaxis, :, np.newaxis], 240, axis=0)
    frame = np.repeat(frame, 3, axis=2)
    cv2.rectangle(frame, (218, 65), (250, 239), (72, 72, 72), -1)

    detector = LaneDetector()
    found, error = detector.process(frame, center_x=160)

    assert found is True
    assert error > 55.0
    assert np.count_nonzero(detector.last_mask) > 0


def test_alt_kenara_uzanmayan_koyu_nesne_serit_sayilmaz():
    frame = np.full((240, 320, 3), 180, dtype=np.uint8)
    cv2.rectangle(frame, (20, 10), (170, 80), (30, 30, 30), -1)

    found, error = LaneDetector().process(frame, center_x=160)

    assert found is False
    assert error == 0.0


def test_onceki_seritle_tutarli_kontur_secilir():
    detector = LaneDetector()
    first = np.full((240, 320, 3), 210, dtype=np.uint8)
    cv2.rectangle(first, (225, 60), (250, 239), (20, 20, 20), -1)
    assert detector.process(first, center_x=160)[0] is True

    second = np.full((240, 320, 3), 210, dtype=np.uint8)
    cv2.rectangle(second, (215, 60), (250, 239), (20, 20, 20), -1)
    cv2.rectangle(second, (5, 40), (105, 239), (20, 20, 20), -1)
    found, error = detector.process(second, center_x=160)

    assert found is True
    assert error > 45.0


def test_ileride_saga_yatmis_serit_pozitif_yon_hatasi_uretir():
    frame = np.full((240, 320, 3), 210, dtype=np.uint8)
    points = np.array([[110, 239], [145, 239], [230, 70], [205, 70]])
    cv2.fillPoly(frame, [points], (20, 20, 20))
    detector = LaneDetector()

    found, _ = detector.process(frame, center_x=160)

    assert found is True
    assert detector.last_heading_error > 0.15


def test_yeni_oturum_onceki_kontur_konumunu_unutur():
    detector = LaneDetector()
    right = np.full((240, 320, 3), 210, dtype=np.uint8)
    cv2.rectangle(right, (235, 60), (270, 239), (20, 20, 20), -1)
    assert detector.process(right, center_x=160)[0] is True

    detector.reset_tracking()
    left = np.full((240, 320, 3), 210, dtype=np.uint8)
    cv2.rectangle(left, (10, 60), (45, 239), (20, 20, 20), -1)
    found, error = detector.process(left, center_x=160)

    assert found is True
    assert error < -100.0


def test_ipm_lookahead_satirinda_serit_merkezini_bulur():
    frame = np.full((240, 320, 3), 210, dtype=np.uint8)
    cv2.rectangle(frame, (215, 40), (245, 239), (20, 20, 20), -1)
    identity = [0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 1.0]
    detector = LaneDetector(
        ipm_enabled=True,
        ipm_source_points=identity,
        ipm_destination_points=identity,
        lookahead_y=150,
        lookahead_band_half_height=4,
    )

    found, _ = detector.process(frame, center_x=160)

    assert found is True
    assert detector.last_lookahead_x == pytest.approx(230.0, abs=1.0)
    assert detector.last_debug_frame is not None


def test_lookahead_satirini_kesmeyen_kontur_pd_olcumu_uretmez():
    frame = np.full((240, 320, 3), 210, dtype=np.uint8)
    cv2.rectangle(frame, (145, 190), (175, 239), (20, 20, 20), -1)
    detector = LaneDetector(lookahead_y=150, lookahead_band_half_height=4)

    found, _ = detector.process(frame, center_x=160)

    assert found is True
    assert detector.last_lookahead_x is None
