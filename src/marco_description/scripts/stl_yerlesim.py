"""Montajin yan ve ust gorunusunu cizer, ana bilesenleri etiketler.

Amaci yon belirsizligini gidermek: parca adlari "On" icin buyuk z diyor ama
catallar kucuk z tarafinda. URDF'in +x yonu bu karara bagli oldugu icin once
yerlesimin gorulmesi gerekiyor.
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

# Ilgi cekici bilesenler: desen -> (etiket, renk)
VURGU = {
    "LdemirÇatal": ("catal", "#e53935"),
    "SarhoşTeker": ("sarhos teker", "#1e88e5"),
    "0002_01_01_00_05-1": ("tahrik tekeri", "#43a047"),
    "Akü": ("aku", "#fb8c00"),
    "ÖnKafes": ("On* kafes", "#8e24aa"),
    "ArkaÜstKapak": ("Arka* ust kapak", "#00acc1"),
}


def uclari_oku(yol: Path, adim: int = 1) -> np.ndarray:
    """Binary STL'den kose noktalarini okur, adim kadar seyreltir."""
    ham = yol.read_bytes()
    sayi = int(np.frombuffer(ham, dtype="<u4", count=1, offset=80)[0])
    kayit = np.dtype(
        [("normal", "<f4", 3), ("koseler", "<f4", (3, 3)), ("oznitelik", "<u2")]
    )
    veri = np.frombuffer(ham, dtype=kayit, count=sayi, offset=84)
    return veri["koseler"].reshape(-1, 3)[::adim].astype(np.float64)


def etiketle(ad: str) -> tuple[str, str] | None:
    """Parca adini vurgu listesiyle eslestirir."""
    for desen, bilgi in VURGU.items():
        if desen in ad:
            return bilgi
    return None


genel: list[np.ndarray] = []
vurgulu: dict[str, list[np.ndarray]] = {}

for yol in sorted(KLASOR.glob("*.STL")):
    n = uclari_oku(yol, adim=7)
    bilgi = etiketle(yol.name)
    if bilgi is None:
        genel.append(n)
    else:
        vurgulu.setdefault(bilgi[0], []).append(n)

genel_n = np.vstack(genel)

fig, eksenler = plt.subplots(2, 1, figsize=(15, 11))

# --- Yan gorunus: z (uzunluk) - y (yukseklik)
ax = eksenler[0]
ax.scatter(genel_n[:, 2], genel_n[:, 1], s=0.4, c="#bdbdbd", alpha=0.5)
for etiket, parcalar in vurgulu.items():
    p = np.vstack(parcalar)
    renk = next(v[1] for v in VURGU.values() if v[0] == etiket)
    ax.scatter(p[:, 2], p[:, 1], s=0.8, c=renk, label=etiket, alpha=0.8)

zemin = 13.778
ax.axhline(zemin, color="black", ls="--", lw=1.2)
ax.text(30, zemin - 22, f"sarhos teker temasi  y={zemin:.1f}", fontsize=9)
ax.axhline(25.27, color="#43a047", ls=":", lw=1.4)
ax.text(700, 25.27 + 8, "tahrik tekeri alti  y=25.3  (11.5 mm YUKARIDA)",
        fontsize=9, color="#2e7d32")
ax.axvline(1171.95, color="#43a047", ls="-.", lw=1.0, alpha=0.6)
ax.text(1180, 480, "tahrik aksi\nz=1172", fontsize=9, color="#2e7d32")

ax.set_xlabel("z  [mm]   (SolidWorks uzunluk ekseni)")
ax.set_ylabel("y  [mm]   (yukseklik)")
ax.set_title("YAN GORUNUS  —  catallar kucuk z'de, parca adlari 'On' icin buyuk z diyor")
ax.set_aspect("equal")
ax.grid(alpha=0.25)
ax.legend(loc="upper left", markerscale=12, fontsize=9)

# --- Ust gorunus: z (uzunluk) - x (genislik)
ax = eksenler[1]
ax.scatter(genel_n[:, 2], genel_n[:, 0], s=0.4, c="#bdbdbd", alpha=0.5)
for etiket, parcalar in vurgulu.items():
    p = np.vstack(parcalar)
    renk = next(v[1] for v in VURGU.values() if v[0] == etiket)
    ax.scatter(p[:, 2], p[:, 0], s=0.8, c=renk, label=etiket, alpha=0.8)

ax.axhline(365.40, color="black", ls="--", lw=1.0, alpha=0.6)
ax.text(30, 375, "govde orta ekseni  x=365.4", fontsize=9)
for x, ad in ((135.40, "tahrik tekeri x=135.4"), (595.40, "tahrik tekeri x=595.4")):
    ax.axhline(x, color="#43a047", ls=":", lw=1.2)
    ax.text(1290, x + 8, ad, fontsize=9, color="#2e7d32")
ax.annotate(
    "", xy=(1172, 135.4), xytext=(1172, 595.4),
    arrowprops=dict(arrowstyle="<->", color="#2e7d32", lw=1.6),
)
ax.text(1190, 365, "teker arasi\n460.0 mm", fontsize=10, color="#2e7d32", weight="bold")

ax.set_xlabel("z  [mm]   (SolidWorks uzunluk ekseni)")
ax.set_ylabel("x  [mm]   (genislik)")
ax.set_title("UST GORUNUS")
ax.set_aspect("equal")
ax.grid(alpha=0.25)

plt.tight_layout()
plt.savefig(CIKTI, dpi=95)
print(f"kaydedildi: {CIKTI}")
