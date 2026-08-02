"""On panellerin dis yuzunu dolu cizerek kesiklerin konumunu olcer.

LiDAR ve kamera on yuze montajlaniyor. Panel plakalarindaki delik/yarik
kesikleri STL'de mevcut oldugundan, dis yuzey ucgenleri dolu cizildiginde
kesikler bosluk olarak gorunur ve koordinatlari okunabilir.

Kullanim:
    python3 stl_on_panel_kesikleri.py <stl_klasoru> <cikti.png>
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402

KLASOR = Path(sys.argv[1])
CIKTI = Path(sys.argv[2])

Z_AKS = 1171.95
X_ORTA = 365.40
Y_ZEMIN = 13.778

PANELLER = [
    ("ÜstKapak-2", "ust kapak (oval + izgara + logo)"),
    ("DM_Ön_Üst-2", "on ust serit"),
    ("DM_Ön_Alt-1", "on alt plaka"),
    ("ÖnAltKapak-1", "on alt kapak"),
]


def ucgenleri_oku(yol: Path) -> np.ndarray:
    """STL'den (N, 3, 3) ucgen dizisini dondurur."""
    ham = yol.read_bytes()
    sayi = int(np.frombuffer(ham, dtype="<u4", count=1, offset=80)[0])
    kayit = np.dtype(
        [("normal", "<f4", 3), ("koseler", "<f4", (3, 3)), ("oznitelik", "<u2")]
    )
    veri = np.frombuffer(ham, dtype=kayit, count=sayi, offset=84)
    return veri["koseler"].astype(np.float64)


fig, eksenler = plt.subplots(1, len(PANELLER), figsize=(22, 8))

for ax, (desen, etiket) in zip(eksenler, PANELLER):
    adaylar = [p for p in KLASOR.glob("*.STL") if desen in p.name]
    if not adaylar:
        ax.set_title(f"{desen}: bulunamadi")
        continue
    ucgen = ucgenleri_oku(adaylar[0])

    x = ucgen[:, :, 2] - Z_AKS  # ileri
    y = ucgen[:, :, 0] - X_ORTA  # sol
    z = ucgen[:, :, 1] - Y_ZEMIN  # yukari

    # Dis yuz: en buyuk x'e yakin, tamami ayni x duzleminde olan ucgenler.
    # Tolerans plaka kalinliginin altinda tutuluyor ki arka yuz karismasin.
    dis = x.max()
    yuzey = np.all(x > dis - 0.6, axis=1)

    poligonlar = [np.column_stack([y[i], z[i]]) for i in np.nonzero(yuzey)[0]]
    ax.add_collection(
        PolyCollection(poligonlar, facecolors="#4a6fa5", edgecolors="none")
    )

    ax.set_xlim(y.min() - 10, y.max() + 10)
    ax.set_ylim(z.min() - 10, z.max() + 10)
    ax.set_aspect("equal")
    ax.set_title(f"{desen}\n{etiket}\nx_urdf = {dis:+.1f} mm, {yuzey.sum()} ucgen")
    ax.set_xlabel("y_urdf [mm]  sol +")
    ax.set_ylabel("z_urdf [mm]  zeminden")
    ax.grid(alpha=0.3, linewidth=0.4)
    ax.set_xticks(np.arange(-300, 301, 50))
    ax.tick_params(labelsize=7)

plt.tight_layout()
plt.savefig(CIKTI, dpi=110)
print(f"kaydedildi: {CIKTI}")
