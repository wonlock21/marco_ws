"""Eski Otsu/HSV deney hattinin zaman icindeki kararliligini olcer.

ROS'a yayin yapmak yerine hatayi biriktirip istatistigini verir. Guncel
imgprocess surus zincirinin parcasi degildir; yalniz karsilastirma aracidir.

Kullanim:
    python3 serit_kararlilik.py [saniye]
"""

from __future__ import annotations

import sys
import time

import cv2
import numpy as np

SURE = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0

# Eski PWM/PD deneyinin karsilastirma sabitleri.
KP, KD, TABAN = 0.10, 0.05, 100.0

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
for _ in range(10):
    cap.read()

cekirdek = np.ones((5, 5), np.uint8)
otsu_hatalari: list[float] = []
hsv_hatalari: list[float] = []
hsv_kayip = 0

baslangic = time.monotonic()
while time.monotonic() - baslangic < SURE:
    ret, kare = cap.read()
    if not ret:
        continue
    merkez_x = kare.shape[1] // 2

    gri = cv2.cvtColor(kare, cv2.COLOR_BGR2GRAY)
    _, otsu = cv2.threshold(gri, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    m = cv2.moments(otsu)
    if m["m00"] > 0:
        otsu_hatalari.append(m["m10"] / m["m00"] - merkez_x)

    hsv = cv2.cvtColor(kare, cv2.COLOR_BGR2HSV)
    maske = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 50]))
    maske = cv2.dilate(cv2.erode(maske, cekirdek, iterations=1), cekirdek, iterations=1)
    konturlar, _ = cv2.findContours(maske, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if konturlar:
        m = cv2.moments(max(konturlar, key=cv2.contourArea))
        if m["m00"] > 0:
            hsv_hatalari.append(m["m10"] / m["m00"] - merkez_x)
        else:
            hsv_kayip += 1
    else:
        hsv_kayip += 1

    time.sleep(0.1)  # Eski deneydeki 10 Hz ornekleme hizi.

cap.release()

print(f"sure {SURE:.0f} s | HSV serit kaybi: {hsv_kayip} kare")
print("=" * 74)
for ad, v in [("OTSU", otsu_hatalari), ("HSV", hsv_hatalari)]:
    if len(v) < 3:
        print(f"{ad}: yeterli veri yok ({len(v)} kare)")
        continue
    a = np.array(v)
    fark = np.diff(a)
    # Kontrolcu dt=0.1 ile calisiyor, yani turev = fark / 0.1 = fark * 10
    d_pwm = KD * np.abs(fark) * 10.0
    p_pwm = KP * np.abs(a)
    print(f"{ad:5} n={len(a):4d}  ortalama={a.mean():+7.1f} px  std={a.std():6.1f} px  "
          f"aralik=[{a.min():+.0f}, {a.max():+.0f}]")
    print(f"      kareler arasi sicrama:  ortalama {np.abs(fark).mean():5.1f} px, "
          f"en buyuk {np.abs(fark).max():5.1f} px")
    print(f"      P terimi katkisi:  ortalama {p_pwm.mean():5.1f} PWM")
    print(f"      D terimi katkisi:  ortalama {d_pwm.mean():5.1f} PWM, "
          f"en buyuk {d_pwm.max():5.1f} PWM   (taban hiz {TABAN:.0f})")
