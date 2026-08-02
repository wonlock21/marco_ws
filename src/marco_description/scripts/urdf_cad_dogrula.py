"""CAD nokta bulutunu URDF cercevesine tasiyip model kutulariyla karsilastirir.

Isaret hatasi (ileri yon, sol/sag) bu ustuste bindirmede aninda gorulur:
kutular nokta bulutuyla ortusmuyorsa donusum yanlistir.

Kullanim:
    python3 urdf_cad_dogrula.py <stl_klasoru> <urdf_dosyasi> <cikti.png>
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as patches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

STL_KLASOR = Path(sys.argv[1])
URDF = Path(sys.argv[2])
CIKTI = Path(sys.argv[3])

# properties.xacro'daki donusum sabitleri
Z_AKS = 1171.95
X_ORTA = 365.40
Y_ZEMIN = 13.778


def uclari_oku(yol: Path, hedef: int = 4000) -> np.ndarray:
    """Binary STL yuzeyinden ~hedef adet nokta ornekler.

    Kose noktalarini cizmek yaniltici: uzun duz yuzeyler az kose tasidigi icin
    catal gibi basit profiller cizimde neredeyse kayboluyor, buna karsilik ince
    kavisli parcalar (sarhos teker, 188 bin ucgen) cizimi boguyor. Bunun yerine
    ucgen yuzeylerinden alana gore agirlikli rastgele nokta ornekleniyor;
    boylece nokta yogunlugu mesh yogunlugundan bagimsiz, yuzey alaniyla
    orantili olur.
    """
    ham = yol.read_bytes()
    sayi = int(np.frombuffer(ham, dtype="<u4", count=1, offset=80)[0])
    kayit = np.dtype(
        [("normal", "<f4", 3), ("koseler", "<f4", (3, 3)), ("oznitelik", "<u2")]
    )
    ucgen = np.frombuffer(ham, dtype=kayit, count=sayi, offset=84)["koseler"]
    ucgen = ucgen.astype(np.float64)

    a, b, c = ucgen[:, 0], ucgen[:, 1], ucgen[:, 2]
    alan = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    toplam = alan.sum()
    if toplam <= 0:
        return a

    rng = np.random.default_rng(0)
    sec = rng.choice(len(ucgen), size=hedef, p=alan / toplam)

    # Ucgen icinde duzgun dagilim icin barisentrik ornekleme
    u = rng.random(hedef)
    v = rng.random(hedef)
    katla = u + v > 1.0
    u[katla], v[katla] = 1.0 - u[katla], 1.0 - v[katla]
    p0, p1, p2 = a[sec], b[sec], c[sec]
    return p0 + u[:, None] * (p1 - p0) + v[:, None] * (p2 - p0)


def urdf_cercevesine(cad: np.ndarray) -> np.ndarray:
    """CAD (mm) noktalarini URDF (m) cercevesine tasir."""
    return np.column_stack(
        [
            (cad[:, 2] - Z_AKS) / 1000.0,
            (cad[:, 0] - X_ORTA) / 1000.0,
            (cad[:, 1] - Y_ZEMIN) / 1000.0,
        ]
    )


noktalar = urdf_cercevesine(
    np.vstack([uclari_oku(p) for p in sorted(STL_KLASOR.glob("*.STL"))])
)

# URDF'ten eklem konumlarini ve kutu/silindir gorsellerini topla
kok = ET.parse(URDF).getroot()
konum: dict[str, np.ndarray] = {"base_link": np.zeros(3)}
eklemler = []
for j in kok.findall("joint"):
    o = j.find("origin")
    xyz = np.array([float(v) for v in (o.get("xyz") if o is not None else "0 0 0").split()])
    eklemler.append((j.find("parent").get("link"), j.find("child").get("link"), xyz))

# base_footprint -> base_link zincirini cozerek base_link'i kok kabul et
for _ in range(6):
    for ebeveyn, cocuk, xyz in eklemler:
        if ebeveyn in konum and cocuk not in konum:
            konum[cocuk] = konum[ebeveyn] + xyz

fig, eksenler = plt.subplots(2, 1, figsize=(15, 11))

ONEMLI = {
    "left_wheel_link": ("sol tahrik tekeri", "#2e7d32"),
    "right_wheel_link": ("sag tahrik tekeri", "#43a047"),
    "front_left_caster_link": ("on sol sarhos", "#1565c0"),
    "front_right_caster_link": ("on sag sarhos", "#1976d2"),
    "rear_left_caster_link": ("arka sol sarhos", "#0288d1"),
    "rear_right_caster_link": ("arka sag sarhos", "#039be5"),
    "fork_link": ("catal koku", "#e53935"),
    "laser_link": ("laser_link (TAHMIN)", "#8e24aa"),
    "camera_front_link": ("on kamera (TAHMIN)", "#f57c00"),
    "camera_rear_link": ("arka kamera (TAHMIN)", "#fb8c00"),
}

# --- Yan gorunus: x (ileri) - z (yukari)
ax = eksenler[0]
ax.scatter(noktalar[:, 0], noktalar[:, 2], s=0.4, c="#c8c8c8", alpha=0.5,
           label="CAD nokta bulutu")
for ad, (etiket, renk) in ONEMLI.items():
    if ad in konum:
        p = konum[ad]
        ax.plot(p[0], p[2], "o", ms=9, color=renk, mec="black", mew=0.6, label=etiket)
ax.axhline(0, color="black", ls="--", lw=1.2)
ax.text(-1.15, -0.045, "zemin (base_footprint)", fontsize=9)
ax.axvline(0, color="#2e7d32", ls="-.", lw=1.0, alpha=0.7)
ax.text(0.02, 0.50, "base_link\n(tahrik aksi)", fontsize=9, color="#2e7d32")
ax.annotate("ILERI", xy=(0.72, 0.47), xytext=(0.30, 0.47),
            arrowprops=dict(arrowstyle="->", lw=2.2, color="#c62828"),
            fontsize=12, color="#c62828", weight="bold", va="center")
ax.set_xlabel("x  [m]   ileri +")
ax.set_ylabel("z  [m]   yukari +")
ax.set_title("YAN GORUNUS  —  CAD nokta bulutu URDF cercevesinde, uzerine URDF cerceveleri")
ax.set_aspect("equal")
ax.grid(alpha=0.25)
ax.legend(loc="upper left", fontsize=8, ncol=2)

# --- Ust gorunus: x (ileri) - y (sol)
ax = eksenler[1]
ax.scatter(noktalar[:, 0], noktalar[:, 1], s=0.4, c="#c8c8c8", alpha=0.5)
for ad, (etiket, renk) in ONEMLI.items():
    if ad in konum:
        p = konum[ad]
        ax.plot(p[0], p[1], "o", ms=9, color=renk, mec="black", mew=0.6)
        if "sarhos" not in etiket:
            ax.annotate(etiket, (p[0], p[1]), textcoords="offset points",
                        xytext=(6, 8), fontsize=8, color=renk)

# Nav2 ayak izi: olculen dis sinirlar
x_alt, x_ust = noktalar[:, 0].min(), noktalar[:, 0].max()
y_alt, y_ust = noktalar[:, 1].min(), noktalar[:, 1].max()
ax.add_patch(patches.Rectangle((x_alt, y_alt), x_ust - x_alt, y_ust - y_alt,
                               fill=False, ec="#c62828", lw=1.8, ls="--"))
ax.text(x_alt, y_ust + 0.03,
        f"olculen dis sinir  x {x_alt:+.3f}..{x_ust:+.3f}   y {y_alt:+.3f}..{y_ust:+.3f}",
        fontsize=9, color="#c62828", weight="bold")
ax.axhline(0, color="black", ls="--", lw=0.9, alpha=0.6)
ax.axvline(0, color="#2e7d32", ls="-.", lw=1.0, alpha=0.7)
ax.annotate("", xy=(0, 0.230), xytext=(0, -0.230),
            arrowprops=dict(arrowstyle="<->", color="#2e7d32", lw=1.8))
ax.text(0.03, 0.0, "teker arasi\n0.460 m", fontsize=9, color="#2e7d32", weight="bold")
ax.set_xlabel("x  [m]   ileri +")
ax.set_ylabel("y  [m]   sol +")
ax.set_title("UST GORUNUS")
ax.set_aspect("equal")
ax.grid(alpha=0.25)

plt.tight_layout()
plt.savefig(CIKTI, dpi=95)

print(f"kaydedildi: {CIKTI}")
print()
print("Nav2 ayak izi icin olculen dis sinirlar (base_link merkezli):")
print(f"  x  {x_alt:+.3f} .. {x_ust:+.3f}   (uzunluk {x_ust-x_alt:.3f} m)")
print(f"  y  {y_alt:+.3f} .. {y_ust:+.3f}   (genislik {y_ust-y_alt:.3f} m)")
print(f"  z  {noktalar[:,2].min():+.3f} .. {noktalar[:,2].max():+.3f}")
