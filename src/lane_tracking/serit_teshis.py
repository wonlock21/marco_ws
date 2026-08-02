"""Tek kare yakalayip tracker.py'nin iki yontemini de gorsellestirir.

tracker.py cv2.imshow kullaniyor; Orange Pi uzerinde pencere acmak hem CPU
yiyor hem uzaktan bakilamiyor. Bu betik ayni islemi yapip sonucu PNG'ye
yazar, boylece tespitin dogru olup olmadigi kayit uzerinden incelenebilir.

Kullanim:
    python3 serit_teshis.py <cikti.png>
"""

from __future__ import annotations

import sys

import cv2
import numpy as np

CIKTI = sys.argv[1] if len(sys.argv) > 1 else "/tmp/serit_teshis.png"

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Ilk kareler otomatik pozlama oturmadan geldigi icin atiliyor.
for _ in range(10):
    cap.read()
ret, kare = cap.read()
cap.release()

if not ret:
    print("kare alinamadi", file=sys.stderr)
    raise SystemExit(1)

yukseklik, genislik, _ = kare.shape
merkez_x = genislik // 2
gosterim = kare.copy()

gri = cv2.cvtColor(kare, cv2.COLOR_BGR2GRAY)
_, otsu = cv2.threshold(gri, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

hsv = cv2.cvtColor(kare, cv2.COLOR_BGR2HSV)
maske = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 50]))
cekirdek = np.ones((5, 5), np.uint8)
maske = cv2.dilate(cv2.erode(maske, cekirdek, iterations=1), cekirdek, iterations=1)

ozet = []

m = cv2.moments(otsu)
if m["m00"] > 0:
    cx, cy = int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"])
    cv2.circle(gosterim, (cx, cy), 8, (0, 0, 255), -1)
    cv2.line(gosterim, (merkez_x, cy), (cx, cy), (0, 0, 255), 2)
    ozet.append(f"OTSU hata = {cx - merkez_x:+d} px")
else:
    ozet.append("OTSU: bolge bulunamadi")

konturlar, _ = cv2.findContours(maske, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
if konturlar:
    enbuyuk = max(konturlar, key=cv2.contourArea)
    m = cv2.moments(enbuyuk)
    if m["m00"] > 0:
        cx, cy = int(m["m10"] / m["m00"]), int(m["m01"] / m["m00"])
        cv2.drawContours(gosterim, [enbuyuk], -1, (0, 255, 0), 2)
        cv2.circle(gosterim, (cx, cy), 10, (0, 255, 0), -1)
        cv2.line(gosterim, (merkez_x, cy), (cx, cy), (0, 255, 0), 2)
        oran = 100.0 * cv2.contourArea(enbuyuk) / (yukseklik * genislik)
        ozet.append(f"HSV  hata = {cx - merkez_x:+d} px, kontur karenin %{oran:.1f}'i")
else:
    ozet.append("HSV: kontur bulunamadi")

cv2.line(gosterim, (merkez_x, 0), (merkez_x, yukseklik), (255, 0, 0), 2)

# Uc gorunumu yan yana koy: ham+isaretli, OTSU maskesi, HSV maskesi.
birlesik = np.hstack(
    [
        gosterim,
        cv2.cvtColor(otsu, cv2.COLOR_GRAY2BGR),
        cv2.cvtColor(maske, cv2.COLOR_GRAY2BGR),
    ]
)
for i, etiket in enumerate(["ham (kirmizi OTSU, yesil HSV)", "OTSU maskesi", "HSV maskesi"]):
    cv2.putText(
        birlesik, etiket, (i * genislik + 8, 20),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1
    )

cv2.imwrite(CIKTI, birlesik)
print("\n".join(ozet))
print(f"kaydedildi: {CIKTI}")
