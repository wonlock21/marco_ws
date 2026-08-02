"""Aracin on ve arka yuzunu karsidan cizer.

Amaci LiDAR ve kamera kesiklerinin hangi panelde oldugunu bulmak: kullanicinin
SolidWorks ekran goruntusuyle karsilastirilip eslesen panel saptanacak, sonra
kesiklerin koordinati olculecek.

Kullanim:
    python3 stl_on_arka_gorunus.py <stl_klasoru> <cikti.png>
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

KLASOR = Path(sys.argv[1])
CIKTI = Path(sys.argv[2])

Z_AKS = 1171.95
X_ORTA = 365.40
Y_ZEMIN = 13.778


def yuzey_ornekle(yol: Path, hedef: int = 20000) -> np.ndarray:
    """STL yuzeyinden alana gore agirlikli nokta ornekler."""
    ham = yol.read_bytes()
    sayi = int(np.frombuffer(ham, dtype="<u4", count=1, offset=80)[0])
    kayit = np.dtype(
        [("normal", "<f4", 3), ("koseler", "<f4", (3, 3)), ("oznitelik", "<u2")]
    )
    ucgen = np.frombuffer(ham, dtype=kayit, count=sayi, offset=84)["koseler"]
    ucgen = ucgen.astype(np.float64)
    a, b, c = ucgen[:, 0], ucgen[:, 1], ucgen[:, 2]
    alan = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    if alan.sum() <= 0:
        return a
    rng = np.random.default_rng(0)
    sec = rng.choice(len(ucgen), size=hedef, p=alan / alan.sum())
    u, v = rng.random(hedef), rng.random(hedef)
    katla = u + v > 1.0
    u[katla], v[katla] = 1.0 - u[katla], 1.0 - v[katla]
    p0, p1, p2 = a[sec], b[sec], c[sec]
    return p0 + u[:, None] * (p1 - p0) + v[:, None] * (p2 - p0)


parcalar = []
for yol in sorted(KLASOR.glob("*.STL")):
    n = yuzey_ornekle(yol)
    parcalar.append((yol.name.replace("GenelMontaj - ", "").replace(".STL", ""), n))

fig, eksenler = plt.subplots(1, 2, figsize=(16, 9))

# On yuz: aracin en buyuk x_urdf tarafi (CAD z buyuk). Yalnizca on 200 mm'lik
# dilimi al, arkadaki yapilar goruntuye karismasin.
for ax, (etiket, kosul) in zip(
    eksenler,
    [
        ("ON YUZ (x_urdf > +0.30)  karsidan", lambda x: x > 300.0),
        ("ARKA (x_urdf < -0.40)  karsidan", lambda x: x < -400.0),
    ],
):
    for ad, n in parcalar:
        x_urdf = n[:, 2] - Z_AKS
        m = kosul(x_urdf)
        if m.sum() < 20:
            continue
        # Karsidan bakis: yatay eksen y_urdf (sol +), dusey z_urdf (yukari +).
        # Onden bakinca sol taraf ekranin sagina gelsin diye y ters cevrilmedi;
        # bakis yonu +x'ten geriye dogru.
        y_urdf = n[m, 0] - X_ORTA
        z_urdf = n[m, 1] - Y_ZEMIN
        ax.scatter(y_urdf, z_urdf, s=0.6, alpha=0.5, label=ad[:34])
    ax.set_title(etiket)
    ax.set_xlabel("y_urdf  [mm]   sol +")
    ax.set_ylabel("z_urdf  [mm]   zeminden yukari")
    ax.set_aspect("equal")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right", fontsize=6, markerscale=8, ncol=2)

plt.tight_layout()
plt.savefig(CIKTI, dpi=100)
print(f"kaydedildi: {CIKTI}")
