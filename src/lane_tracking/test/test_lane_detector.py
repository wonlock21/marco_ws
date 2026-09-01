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


def test_kalin_seridin_ayrilan_kenarlari_merkeze_donusturulur():
    frame = np.full((240, 320, 3), 180, dtype=np.uint8)
    cv2.rectangle(frame, (190, 0), (270, 239), (100, 100, 100), -1)
    detector = LaneDetector(
        block_size=81,
        adaptive_offset=20,
        lookahead_y=150,
        lookahead_band_half_height=4,
    )

    found, _ = detector.process(frame, center_x=160)

    assert found is True
    assert detector.last_lookahead_x == pytest.approx(230.0, abs=2.0)
    assert np.all(detector.last_mask[150, 195:266] == 255)


def test_ince_serit_genisletilmeden_merkezi_korunur():
    frame = np.full((240, 320, 3), 210, dtype=np.uint8)
    cv2.rectangle(frame, (220, 0), (244, 239), (20, 20, 20), -1)
    detector = LaneDetector(block_size=81, lookahead_y=150)

    found, _ = detector.process(frame, center_x=160)

    assert found is True
    assert detector.last_lookahead_x == pytest.approx(232.0, abs=1.0)


def test_seride_baglanan_yatay_zemin_lekesi_merkezi_kaydirmiyor():
    frame = np.full((240, 320, 3), 180, dtype=np.uint8)
    cv2.rectangle(frame, (190, 0), (270, 239), (100, 100, 100), -1)
    cv2.rectangle(frame, (70, 140), (190, 160), (105, 105, 105), -1)
    detector = LaneDetector(
        block_size=81,
        adaptive_offset=20,
        lookahead_y=150,
        lookahead_band_half_height=5,
    )

    found, _ = detector.process(frame, center_x=160)

    assert found is True
    assert detector.last_lookahead_x == pytest.approx(230.0, abs=2.0)
    assert np.count_nonzero(detector.last_mask[150, 70:170]) == 0


def test_lookahead_satirini_kesmeyen_kontur_pd_olcumu_uretmez():
    frame = np.full((240, 320, 3), 210, dtype=np.uint8)
    cv2.rectangle(frame, (145, 190), (175, 239), (20, 20, 20), -1)
    detector = LaneDetector(lookahead_y=150, lookahead_band_half_height=4)

    found, _ = detector.process(frame, center_x=160)

    assert found is True
    assert detector.last_lookahead_x is None


def test_egik_kalin_seridin_tam_govdesi_ve_orta_noktasi_kullanilir():
    frame = np.full((240, 320, 3), 190, dtype=np.uint8)
    lane = np.array([[120, 239], [205, 239], [270, 20], [190, 20]])
    cv2.fillPoly(frame, [lane], (85, 85, 85))
    detector = LaneDetector(
        block_size=81, adaptive_offset=20,
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


def test_kisa_zemin_cizgileri_kalin_seridin_merkezini_bozmaz():
    frame = np.full((240, 320, 3), 190, dtype=np.uint8)
    cv2.rectangle(frame, (195, 0), (270, 239), (80, 80, 80), -1)
    cv2.rectangle(frame, (45, 142), (195, 158), (75, 75, 75), -1)
    cv2.rectangle(frame, (270, 95), (310, 103), (70, 70, 70), -1)
    cv2.rectangle(frame, (20, 205), (75, 212), (65, 65, 65), -1)
    detector = LaneDetector(
        block_size=81, adaptive_offset=20,
        lookahead_y=150, lookahead_band_half_height=5)

    found, _ = detector.process(frame, center_x=160)

    assert found is True
    assert detector.last_lookahead_x == pytest.approx(232.5, abs=3.0)
    assert np.count_nonzero(
        detector.last_selected_mask[150, 45:175]) == 0


def test_ince_adaptif_kenarlar_acilmadan_once_birlestirilir():
    mask = np.zeros((240, 320), dtype=np.uint8)
    mask[:, 190:192] = 255
    mask[:, 268:270] = 255

    recovered = LaneDetector(block_size=81)._recover_wide_lane(mask)

    assert np.all(recovered[120, 190:270] == 255)


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
    frame = np.full((240, 320, 3), 210, dtype=np.uint8)
    lane = np.array([[120, 239], [160, 239], [220, 20], [180, 20]])
    cv2.fillPoly(frame, [lane], (20, 20, 20))
    detector = LaneDetector(lookahead_y=150)

    found, _ = detector.process(frame, center_x=160)

    assert found is True
    assert detector.last_heading_error > 0.10
