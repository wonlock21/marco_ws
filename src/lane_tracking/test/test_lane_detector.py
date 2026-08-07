"""Serit algilayicinin temel davranis testleri."""

import cv2
import numpy as np

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
