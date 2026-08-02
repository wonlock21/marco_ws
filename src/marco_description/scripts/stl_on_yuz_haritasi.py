"""Aracin on yuzunu tek karede dolu cizer ve kesiklerin koordinatini olcer.

Kullanicinin SolidWorks ekran goruntusuyle dogrudan karsilastirilabilir bir
gorunum uretir, ayrica panellerdeki her kesigin sinir kutusunu sayisal olarak
yazdirir. LiDAR ve kamera cerceve konumlari bu ciktidan turetilir.

Kullanim:
    python3 stl_on_yuz_haritasi.py <stl_klasoru> <cikti.png>
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


def ucgenleri_oku(yol: Path) -> np.ndarray:
    """STL'den (N, 3, 3) ucgen dizisini dondurur."""
    ham = yol.read_bytes()
    sayi = int(np.frombuffer(ham, dtype="<u4", count=1, offset=80)[0])
    kayit = np.dtype(
        [("normal", "<f4", 3), ("koseler", "<f4", (3, 3)), ("oznitelik", "<u2")]
    )
    return np.frombuffer(ham, dtype=kayit, count=sayi, offset=84)["koseler"].astype(
        np.float64
    )


def kesikleri_bul(y: np.ndarray, z: np.ndarray, adim: float = 2.0) -> list:
    """Dolu yuzeyi rasterleyip bagli bos bolgelerin sinir kutusunu dondurur."""
    from matplotlib.path import Path as MplPath
    from scipy import ndimage

    y0, y1 = y.min(), y.max()
    z0, z1 = z.min(), z.max()
    yy, zz = np.meshgrid(
        np.arange(y0, y1, adim) + adim / 2, np.arange(z0, z1, adim) + adim / 2
    )
    noktalar = np.column_stack([yy.ravel(), zz.ravel()])
    dolu = np.zeros(len(noktalar), dtype=bool)
    for i in range(len(y)):
        ucgen = MplPath(np.column_stack([y[i], z[i]]))
        dolu |= ucgen.contains_points(noktalar)
    dolu = dolu.reshape(yy.shape)

    # Panelin dis sinirini bos bolge saymamak icin kenardan baglantili
    # boslugu ayikla; kalan bosluklar gercek kesiklerdir.
    bos = ~dolu
    etiket, sayi = ndimage.label(bos)
    dis = set(etiket[0, :]) | set(etiket[-1, :]) | set(etiket[:, 0]) | set(etiket[:, -1])

    kutular = []
    for k in range(1, sayi + 1):
        if k in dis:
            continue
        m = etiket == k
        if m.sum() < 4:
            continue
        kutular.append(
            {
                "y": (yy[m].min() - adim / 2, yy[m].max() + adim / 2),
                "z": (zz[m].min() - adim / 2, zz[m].max() + adim / 2),
                "alan": m.sum() * adim * adim,
            }
        )
    return sorted(kutular, key=lambda k: -k["alan"])


fig, ax = plt.subplots(figsize=(13, 11))
renkler = plt.cm.tab20(np.linspace(0, 1, 20))

print("=" * 96)
print("ON YUZ KESIKLERI  (URDF mm, y_urdf sol +, z_urdf zeminden yukari)")
print("=" * 96)

for indeks, yol in enumerate(sorted(KLASOR.glob("*.STL"))):
    ucgen = ucgenleri_oku(yol)
    x = ucgen[:, :, 2] - Z_AKS
    if x.max() < 380.0:  # yalnizca on kabuk panelleri
        continue

    y = ucgen[:, :, 0] - X_ORTA
    z = ucgen[:, :, 1] - Y_ZEMIN
    yuzey = np.all(x > x.max() - 0.6, axis=1)
    if yuzey.sum() < 4:
        continue

    ad = yol.name.replace("GenelMontaj - ", "").replace(".STL", "")
    ax.add_collection(
        PolyCollection(
            [np.column_stack([y[i], z[i]]) for i in np.nonzero(yuzey)[0]],
            facecolors=renkler[indeks % 20],
            edgecolors="none",
            alpha=0.85,
            label=ad,
        )
    )

    kutular = kesikleri_bul(y[yuzey], z[yuzey])
    if not kutular:
        continue
    print(f"\n{ad}   dis yuz x_urdf = {x.max():+.1f} mm")
    for k in kutular:
        gy = k["y"][1] - k["y"][0]
        gz = k["z"][1] - k["z"][0]
        oy = (k["y"][0] + k["y"][1]) / 2
        oz = (k["z"][0] + k["z"][1]) / 2
        print(
            f"    kesik {gy:6.1f} x {gz:6.1f} mm   merkez y={oy:+7.1f}  z={oz:+7.1f}"
        )
        ax.add_patch(
            plt.Rectangle(
                (k["y"][0], k["z"][0]), gy, gz, fill=False, ec="red", lw=1.4, zorder=5
            )
        )
        ax.annotate(
            f"y{oy:+.0f}\nz{oz:+.0f}",
            (oy, oz),
            color="red",
            fontsize=7,
            ha="center",
            va="center",
            zorder=6,
        )

ax.set_xlim(-340, 340)
ax.set_ylim(0, 560)
ax.set_aspect("equal")
ax.set_title("MarCO on yuz (karsidan) — kirmizi: panel kesikleri")
ax.set_xlabel("y_urdf [mm]   sol +")
ax.set_ylabel("z_urdf [mm]   zeminden yukari")
ax.grid(alpha=0.3, linewidth=0.4)
ax.legend(loc="lower left", fontsize=7)
plt.tight_layout()
plt.savefig(CIKTI, dpi=110)
print(f"\nkaydedildi: {CIKTI}")
