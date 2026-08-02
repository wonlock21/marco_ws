"""Belirli STL parcalarinin geometrisini ayrintili inceler.

Sinir kutusu bir parcanin silindir mi plaka mi oldugunu ayirt etmez. Bu betik
tekerlek adaylarinin donme eksenini ve gercek yaricapini cikarir, ayrica zemine
temas eden parcalari bulur. URDF'e yazilacak wheel_radius ve wheel_separation
degerleri buradan gelir.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

KLASOR = Path(sys.argv[1] if len(sys.argv) > 1 else ".")


def uclari_oku(yol: Path) -> np.ndarray:
    """Binary STL dosyasindan ucgen kose noktalarini (N, 3) olarak dondurur."""
    ham = yol.read_bytes()
    sayi = int(np.frombuffer(ham, dtype="<u4", count=1, offset=80)[0])
    kayit = np.dtype(
        [("normal", "<f4", 3), ("koseler", "<f4", (3, 3)), ("oznitelik", "<u2")]
    )
    veri = np.frombuffer(ham, dtype=kayit, count=sayi, offset=84)
    return veri["koseler"].reshape(-1, 3).astype(np.float64)


def bul(desen: str) -> list[Path]:
    """Ada gore parca dosyalarini bulur."""
    return sorted(p for p in KLASOR.glob("*.STL") if desen in p.name)


def silindir_incele(ad: str, yol: Path) -> None:
    """Parcanin x eksenine dik kesitini olcerek yaricap ve eksen konumu verir."""
    n = uclari_oku(yol)
    alt, ust = n.min(axis=0), n.max(axis=0)

    # x ekseni etrafinda dondugu varsayimiyla y-z kesitinde en uzak nokta
    merkez_y = (alt[1] + ust[1]) / 2.0
    merkez_z = (alt[2] + ust[2]) / 2.0
    yaricaplar = np.hypot(n[:, 1] - merkez_y, n[:, 2] - merkez_z)

    print(f"\n--- {ad}")
    print(f"  dosya       : {yol.name}")
    print(f"  x aralik    : {alt[0]:8.2f} .. {ust[0]:8.2f}   (genislik {ust[0]-alt[0]:.2f})")
    print(f"  y aralik    : {alt[1]:8.2f} .. {ust[1]:8.2f}")
    print(f"  z aralik    : {alt[2]:8.2f} .. {ust[2]:8.2f}")
    print(f"  eksen (y,z) : {merkez_y:.2f}, {merkez_z:.2f}")
    dilim99 = np.percentile(yaricaplar, 99)
    print(f"  yaricap     : max {yaricaplar.max():.2f}  |  %99 dilim {dilim99:.2f}")
    # Kesitin gercekten dairesel olup olmadigi: dis kabuktaki noktalarin
    # yaricap sacilimi kucukse silindir, buyukse plaka/prizma.
    dis = yaricaplar[yaricaplar > yaricaplar.max() * 0.95]
    print(f"  dis kabuk   : {len(dis)} nokta, std {dis.std():.3f} mm -> "
          f"{'SILINDIR' if dis.std() < 1.0 else 'silindir degil'}")


print("=" * 78)
print("TEKERLEK ADAYLARI")
print("=" * 78)

for desen, etiket in [
    ("0002_01_01_00_05-1", "aday A (Q200 x 50)"),
    ("0002_01_01_00_06-1", "aday B (Q160 x 90)"),
]:
    for yol in bul(desen):
        # Montaj ornegi -1 kucuk x'te, -2 buyuk x'te. URDF'te sol yon +y ve
        # y_urdf = x_cad - 365.40 oldugundan -1 SAG, -2 SOL tekerdir.
        # Sezginin tersi; etiketi ezberden yazma.
        yon = "SAG" if "00_00-1" in yol.name else "SOL"
        silindir_incele(f"{etiket}  [{yon}]", yol)

print()
print("=" * 78)
print("ZEMINE EN YAKIN PARCALAR  (en kucuk y)")
print("=" * 78)

satirlar = []
for yol in sorted(KLASOR.glob("*.STL")):
    n = uclari_oku(yol)
    satirlar.append((float(n[:, 1].min()), yol.name, n.min(axis=0), n.max(axis=0)))

for ymin, ad, alt, ust in sorted(satirlar)[:8]:
    kisa = ad.replace("GenelMontaj - ", "").replace(".STL", "")[:46]
    print(f"  y_min {ymin:7.2f}   z {alt[2]:7.1f}..{ust[2]:7.1f}   "
          f"x {alt[0]:6.1f}..{ust[0]:6.1f}   {kisa}")
