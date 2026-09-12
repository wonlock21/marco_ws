"""Turuncu serit algilayicisinin temel davranis testleri."""

import cv2
import numpy as np
import pytest

from lane_tracking.lane_detector import (
    LaneDetector,
    hybrid_orange_lane_mask_cpu,
)


BLUE = (255, 0, 0)
ORANGE = (0, 140, 255)
CAMERA_SALMON = (97, 110, 255)


def blue_frame(height=240, width=320):
    frame = np.empty((height, width, 3), dtype=np.uint8)
    frame[:] = BLUE
    return frame


def test_serit_yokken_bulunamadi_doner():
    found, error = LaneDetector().process(blue_frame(), center_x=160)

    assert found is False
    assert error == 0.0


def test_sagdaki_turuncu_serit_pozitif_hata_uretir():
    frame = blue_frame()
    cv2.rectangle(frame, (210, 80), (250, 239), ORANGE, -1)

    found, error = LaneDetector().process(frame, center_x=160)

    assert found is True
    assert 65.0 <= error <= 75.0


def test_hsv_maskesi_turuncuyu_secer_mavi_zemini_reddeder():
    frame = blue_frame()
    cv2.rectangle(frame, (120, 0), (180, 239), ORANGE, -1)

    mask = hybrid_orange_lane_mask_cpu(frame)

    assert np.count_nonzero(mask[:, 130:171]) > 9000
    assert np.count_nonzero(mask[:, :80]) == 0

def test_kamerada_kirmiziya_kayan_turuncu_seridi_secer():
    frame = blue_frame()
    cv2.rectangle(frame, (120, 0), (180, 239), CAMERA_SALMON, -1)

    mask = hybrid_orange_lane_mask_cpu(frame)

    assert np.count_nonzero(mask[:, 130:171]) > 9000
    assert np.count_nonzero(mask[:, :80]) == 0


def test_turuncu_yokken_sobel_yedegi_seridi_bulur():
    frame = np.full((240, 320, 3), 210, dtype=np.uint8)
    cv2.rectangle(frame, (210, 60), (250, 239), (20, 20, 20), -1)

    detector = LaneDetector()
    found, error = detector.process(frame, center_x=160)

    assert found is True
    assert error > 55.0
    assert np.count_nonzero(detector.last_raw_mask) > 0


def test_alt_kenara_uzanmayan_turuncu_nesne_serit_sayilmaz():
    frame = blue_frame()
    cv2.rectangle(frame, (20, 10), (170, 80), ORANGE, -1)

    found, error = LaneDetector().process(frame, center_x=160)

    assert found is False
    assert error == 0.0


def test_onceki_seritle_tutarli_kontur_secilir():
    detector = LaneDetector()
    first = blue_frame()
    cv2.rectangle(first, (225, 60), (250, 239), ORANGE, -1)
    assert detector.process(first, center_x=160)[0] is True

    second = blue_frame()
    cv2.rectangle(second, (215, 60), (250, 239), ORANGE, -1)
    cv2.rectangle(second, (5, 40), (105, 239), ORANGE, -1)
    found, error = detector.process(second, center_x=160)

    assert found is True
    assert error > 45.0


def test_ileride_saga_yatmis_serit_pozitif_yon_hatasi_uretir():
    frame = blue_frame()
    points = np.array([[110, 239], [145, 239], [230, 70], [205, 70]])
    cv2.fillPoly(frame, [points], ORANGE)
    detector = LaneDetector()

    found, _ = detector.process(frame, center_x=160)

    assert found is True
    assert detector.last_heading_error > 0.15


def test_ust_bant_yokken_kontur_ekseni_serit_egimini_korur():
    contour = np.array(
        [[[90, 239]], [[130, 239]], [[180, 170]], [[150, 170]]],
        dtype=np.int32,
    )

    centers = LaneDetector._fit_contour_axis(
        contour, width=320, near_y=202, far_y=130)

    assert centers is not None
    near_x, far_x = centers
    assert far_x > near_x + 25.0


def test_yeni_oturum_onceki_kontur_konumunu_unutur():
    detector = LaneDetector()
    right = blue_frame()
    cv2.rectangle(right, (235, 60), (270, 239), ORANGE, -1)
    assert detector.process(right, center_x=160)[0] is True

    detector.reset_tracking()
    left = blue_frame()
    cv2.rectangle(left, (10, 60), (45, 239), ORANGE, -1)
    found, error = detector.process(left, center_x=160)

    assert found is True
    assert error < -100.0


def test_ipm_lookahead_satirinda_serit_merkezini_bulur():
    frame = blue_frame()
    cv2.rectangle(frame, (215, 40), (245, 239), ORANGE, -1)
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
    frame = blue_frame()
    cv2.rectangle(frame, (145, 190), (175, 239), ORANGE, -1)
    detector = LaneDetector(lookahead_y=150, lookahead_band_half_height=4)

    found, _ = detector.process(frame, center_x=160)

    assert found is True
    assert detector.last_lookahead_x is None


def test_egik_kalin_seridin_tam_govdesi_ve_orta_noktasi_kullanilir():
    frame = blue_frame()
    lane = np.array([[120, 239], [205, 239], [270, 20], [190, 20]])
    cv2.fillPoly(frame, [lane], ORANGE)
    detector = LaneDetector(
        lookahead_y=150, lookahead_band_half_height=4)

    found, _ = detector.process(frame, center_x=160)

    expected_center = 0.5 * (
        np.interp(150, [20, 239], [190, 120])
        + np.interp(150, [20, 239], [270, 205]))
    assert found is True
    assert detector.last_lookahead_x == pytest.approx(
        expected_center, abs=4.0)
    row = np.flatnonzero(detector.last_selected_mask[150])
    assert row.size >= 65
    assert float(row[0] + row[-1]) * 0.5 == pytest.approx(
        expected_center, abs=4.0)


def test_seride_baglanan_yatay_turuncu_leke_merkezi_kaydirmiyor():
    frame = blue_frame()
    cv2.rectangle(frame, (195, 0), (270, 239), ORANGE, -1)
    cv2.rectangle(frame, (45, 142), (195, 158), ORANGE, -1)
    detector = LaneDetector(
        lookahead_y=150, lookahead_band_half_height=5)

    found, _ = detector.process(frame, center_x=160)

    assert found is True
    assert detector.last_lookahead_x == pytest.approx(232.5, abs=3.0)
    assert np.count_nonzero(
        detector.last_selected_mask[150, 45:175]) == 0


def test_seride_baglanan_orta_uzunluktaki_cizgi_govdeden_atilir():
    component = np.zeros((240, 640), dtype=np.uint8)
    component[:, 250:371] = 255
    component[150:166, 180:250] = 255

    cleaned = LaneDetector._clean_lane_body(component)

    assert np.all(cleaned[158, 250:371] == 255)
    assert np.count_nonzero(cleaned[158, 180:245]) == 0


def test_ince_yatay_iz_serit_sinirinda_cikinti_birakmaz():
    component = np.zeros((240, 640), dtype=np.uint8)
    component[:, 250:371] = 255
    component[145:155, 238:250] = 255

    cleaned = LaneDetector._clean_lane_body(component)

    assert np.all(cleaned[150, 250:371] == 255)
    assert np.count_nonzero(cleaned[150, 238:250]) == 0


def test_uzun_bagli_leke_serit_genisligi_sayilmaz():
    component = np.zeros((480, 640), dtype=np.uint8)
    component[:, 300:421] = 255
    component[90:390, 421:575] = 255

    cleaned = LaneDetector._clean_lane_body(component)

    assert np.all(cleaned[240, 300:421] == 255)
    assert np.count_nonzero(cleaned[240, 430:575]) == 0
    assert LaneDetector._band_center(cleaned, 220, 260) == pytest.approx(
        360.0, abs=1.0)


def test_temiz_seritte_egim_dolu_govde_bant_merkezlerinden_hesaplanir():
    frame = blue_frame()
    lane = np.array([[120, 239], [160, 239], [220, 20], [180, 20]])
    cv2.fillPoly(frame, [lane], ORANGE)
    detector = LaneDetector(lookahead_y=150)

    found, _ = detector.process(frame, center_x=160)

    assert found is True
    assert detector.last_heading_error > 0.10
