"""Ayni kareler uzerinde uc serit tespit yontemini karsilastirir.

Farkli kosturmalarda olculen sayilar kiyaslanamaz, cunku sahne ve el titremesi
degisiyor. Bu betik her kareyi uc yontemle birden isler, boylece aradaki fark
yalnizca yonteme ait olur.

  1) OTSU (tum kare)    : eski deney, esiklenmis goruntunun agirlik merkezi
  2) HSV  (tum kare)    : eski deney, en buyuk konturun agirlik merkezi
  3) HSV  (alt serit)   : ayni ama yalnizca karenin alt %40'i
  4) OTSU + kontur      : OTSU maskesi uzerinde en buyuk kontur
  5) OTSU + kontur, alt : ayni, yalnizca alt serit

4 ve 5 ikisinin gucunu birlestirir: esik aydinlatmaya gore kendini ayarlar
(OTSU), ama sonuc tek bir tutarli bloktan gelir ve blok bulunamazsa yontem
"serit yok" diyebilir (kontur). Sabit HSV esigi bu bantta calismiyor.

Alt serit, aracin hemen onundeki zemine bakar; ileride baslayan bir viraj
hatayi kirletmez.

Kullanim:
    python3 serit_yontem_kiyas.py [saniye]
"""

from __future__ import annotations

import sys
import time

import cv2
import numpy as np

SURE = float(sys.argv[1]) if len(sys.argv) > 1 else 20.0
ROI_ORAN = 0.40  # karenin alt yuzdesi
KP, KD = 0.10, 0.05


def hsv_maskesi(kare: np.ndarray, cekirdek: np.ndarray) -> np.ndarray:
    """Eski HSV deneyindeki siyah maske ve gurultu temizligi."""
    hsv = cv2.cvtColor(kare, cv2.COLOR_BGR2HSV)
    maske = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 50]))
    return cv2.dilate(cv2.erode(maske, cekirdek, iterations=1), cekirdek, iterations=1)


def kontur_merkezi(maske: np.ndarray) -> tuple[float, float] | None:
    """En buyuk konturun x merkezini ve alanini dondurur."""
    konturlar, _ = cv2.findContours(maske, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if not konturlar:
        return None
    enbuyuk = max(konturlar, key=cv2.contourArea)
    m = cv2.moments(enbuyuk)
    if m["m00"] <= 0:
        return None
    return m["m10"] / m["m00"], cv2.contourArea(enbuyuk)


cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
for _ in range(10):
    cap.read()

cekirdek = np.ones((5, 5), np.uint8)
sonuc: dict[str, list[float]] = {
    "OTSU tum kare": [],
    "HSV tum kare": [],
    "HSV alt serit": [],
    "OTSU+kontur": [],
    "OTSU+kontur alt": [],
}
kayip = {ad: 0 for ad in sonuc}
alanlar: list[float] = []

baslangic = time.monotonic()
while time.monotonic() - baslangic < SURE:
    ret, kare = cap.read()
    if not ret:
        continue
    yukseklik, genislik, _ = kare.shape
    merkez_x = genislik // 2

    gri = cv2.cvtColor(kare, cv2.COLOR_BGR2GRAY)
    _, otsu = cv2.threshold(gri, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    m = cv2.moments(otsu)
    if m["m00"] > 0:
        sonuc["OTSU tum kare"].append(m["m10"] / m["m00"] - merkez_x)
    else:
        kayip["OTSU tum kare"] += 1

    maske = hsv_maskesi(kare, cekirdek)
    bulgu = kontur_merkezi(maske)
    if bulgu:
        sonuc["HSV tum kare"].append(bulgu[0] - merkez_x)
        alanlar.append(100.0 * bulgu[1] / (yukseklik * genislik))
    else:
        kayip["HSV tum kare"] += 1

    ust = int(yukseklik * (1.0 - ROI_ORAN))

    bulgu = kontur_merkezi(maske[ust:, :])
    if bulgu:
        sonuc["HSV alt serit"].append(bulgu[0] - merkez_x)
    else:
        kayip["HSV alt serit"] += 1

    # OTSU maskesi de HSV'yle ayni gurultu temizliginden gecirilmeli, yoksa
    # kontur secimi tek piksellik lekelere takilir.
    otsu_temiz = cv2.dilate(
        cv2.erode(otsu, cekirdek, iterations=1), cekirdek, iterations=1
    )
    bulgu = kontur_merkezi(otsu_temiz)
    if bulgu:
        sonuc["OTSU+kontur"].append(bulgu[0] - merkez_x)
    else:
        kayip["OTSU+kontur"] += 1

    bulgu = kontur_merkezi(otsu_temiz[ust:, :])
    if bulgu:
        sonuc["OTSU+kontur alt"].append(bulgu[0] - merkez_x)
    else:
        kayip["OTSU+kontur alt"] += 1

    time.sleep(0.1)

cap.release()

if alanlar:
    print(f"gorulen serit konturu karenin ortalama %{np.mean(alanlar):.1f}'i")
print(f"alt serit = karenin alt %{ROI_ORAN*100:.0f}'i\n")
print(f"{'yontem':<16}{'std':>9}{'sicrama ort':>13}{'sicrama max':>13}"
      f"{'D max PWM':>12}{'kayip':>8}")
print("-" * 71)
for ad, v in sonuc.items():
    if len(v) < 3:
        print(f"{ad:<16}   yeterli veri yok ({len(v)} kare)")
        continue
    a = np.array(v)
    f = np.abs(np.diff(a))
    print(f"{ad:<16}{a.std():8.1f}{f.mean():12.1f}{f.max():13.1f}"
          f"{KD*f.max()*10:12.1f}{kayip[ad]:8d}")
