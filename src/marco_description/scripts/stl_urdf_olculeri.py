"""STL montajindan URDF parametrelerini cikarir.

Cikti dogrudan properties.xacro'ya yazilacak degerlerdir. Olcum yontemi:
parcalar montaj koordinatlarinda ihrac edildigi icin konumlar mutlaktir.

SolidWorks eksenleri (olcumle saptandi):
    x = genislik, y = yukseklik (yukari +), z = uzunluk

Zemin duzlemi sarhos tekerlerin temas noktasidir. Tahrik tekerleri CAD'de
zeminden 11.5 mm yukarida durur; bu bir hata degil, tahrik unitesi yayli
oldugu icin serbest konumda cizilmis olmasindandir (yaylar dogrulanir).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

KLASOR = Path(sys.argv[1])


def uclari_oku(yol: Path) -> np.ndarray:
    """Binary STL'den kose noktalarini (N, 3) olarak okur."""
    ham = yol.read_bytes()
    sayi = int(np.frombuffer(ham, dtype="<u4", count=1, offset=80)[0])
    kayit = np.dtype(
        [("normal", "<f4", 3), ("koseler", "<f4", (3, 3)), ("oznitelik", "<u2")]
    )
    veri = np.frombuffer(ham, dtype=kayit, count=sayi, offset=84)
    return veri["koseler"].reshape(-1, 3).astype(np.float64)


def parca(desen: str) -> list[tuple[str, np.ndarray]]:
    """Ada gore parcalari okur."""
    return [
        (p.name.replace("GenelMontaj - ", "").replace(".STL", ""), uclari_oku(p))
        for p in sorted(KLASOR.glob("*.STL"))
        if desen in p.name
    ]


def kutu(n: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sinir kutusunun alt, ust ve merkezini dondurur."""
    alt, ust = n.min(axis=0), n.max(axis=0)
    return alt, ust, (alt + ust) / 2.0


print("=" * 76)
print("1. YAY DOGRULAMA  (tahrik unitesi yayli mi?)")
print("=" * 76)
yaylar = parca("0002_01_01_01_09-1") + parca("0002_01_01_01_10-1")
if not yaylar:
    # 75 bin ucgenli, ince ve uzun parcalari tara
    for p in sorted(KLASOR.glob("*.STL")):
        n = uclari_oku(p)
        alt, ust, _ = kutu(n)
        olcu = ust - alt
        if len(n) // 3 > 50000 and 20 < olcu[1] < 120 and olcu[0] < 30:
            yaylar.append((p.name.replace("GenelMontaj - ", "")[:44], n))

for ad, n in yaylar:
    alt, ust, mrk = kutu(n)
    # Yay: y ekseni boyunca kesitte sabit yaricapli sarmal -> her y diliminde
    # nokta var ve x-z kesiti dairesel bir tel
    print(f"  {ad[:46]:<48} olcu {(ust-alt)[0]:5.1f} x {(ust-alt)[1]:5.1f} x "
          f"{(ust-alt)[2]:5.1f}  ucgen {len(n)//3:6d}  merkez z={mrk[2]:7.1f}")

print()
print("=" * 76)
print("2. ZEMIN VE TAHRIK TEKERI")
print("=" * 76)
sarhos = parca("SarhoşTeker")
zemin = min(kutu(n)[0][1] for _, n in sarhos)
teker = parca("0002_01_01_00_05-1")
teker_alt = min(kutu(n)[0][1] for _, n in teker)
teker_mrk = np.mean([kutu(n)[2] for _, n in teker], axis=0)
print(f"  zemin (sarhos teker temasi) y = {zemin:.3f} mm")
print(f"  tahrik tekeri alti          y = {teker_alt:.3f} mm")
print(f"  bosluk (yay serbest kursu)    = {teker_alt - zemin:.3f} mm")
print(f"  tahrik aksi                   y = {teker_mrk[1]:.2f}, z = {teker_mrk[2]:.2f}")

x_ler = sorted(kutu(n)[2][0] for _, n in teker)
print(f"  teker merkezleri            x = {x_ler[0]:.2f} / {x_ler[1]:.2f}")
print(f"  TEKER ARASI                   = {x_ler[1] - x_ler[0]:.2f} mm")

print()
print("=" * 76)
print("3. SARHOS TEKERLER  (zemin duzlemini bunlar tanimliyor)")
print("=" * 76)
for ad, n in sarhos:
    alt, ust, mrk = kutu(n)
    print(f"  {ad:<16} x={mrk[0]:7.2f}  z={mrk[2]:7.2f}  "
          f"y {alt[1]:6.2f}..{ust[1]:6.2f}")

print()
print("=" * 76)
print("4. CATAL")
print("=" * 76)
catallar = parca("LdemirÇatal")
for ad, n in catallar:
    alt, ust, mrk = kutu(n)
    print(f"  {ad:<40} x={mrk[0]:7.2f}  z {alt[2]:7.1f}..{ust[2]:7.1f}  "
          f"y {alt[1]:6.2f}..{ust[1]:6.2f}")
cx = sorted(kutu(n)[2][0] for _, n in catallar)
print(f"  dis arasi merkez mesafesi     = {cx[1] - cx[0]:.2f} mm")
c_alt, c_ust, _ = kutu(catallar[0][1])
print(f"  tek dis genisligi             = {(c_ust - c_alt)[0]:.2f} mm")
print(f"  dis uzunlugu                  = {(c_ust - c_alt)[2]:.2f} mm")
print(f"  dis altinin zeminden yuksekligi = {c_alt[1] - zemin:.2f} mm")

print()
print("=" * 76)
print("5. GOVDE VE TOPLAM")
print("=" * 76)
tum_alt = np.array([1e9, 1e9, 1e9])
tum_ust = np.array([-1e9, -1e9, -1e9])
for p in sorted(KLASOR.glob("*.STL")):
    a, u, _ = kutu(uclari_oku(p))
    tum_alt = np.minimum(tum_alt, a)
    tum_ust = np.maximum(tum_ust, u)
print(f"  toplam uzunluk (z)            = {tum_ust[2] - tum_alt[2]:.1f} mm")
print(f"  toplam genislik (x)           = {tum_ust[0] - tum_alt[0]:.1f} mm")
print(f"  zeminden toplam yukseklik     = {tum_ust[1] - zemin:.1f} mm")
print(f"  z aralik                      = {tum_alt[2]:.1f} .. {tum_ust[2]:.1f}")
print(f"  x aralik                      = {tum_alt[0]:.1f} .. {tum_ust[0]:.1f}")

for desen in ("Taban-1", "DM_Yan_Parçalar-1", "Akü-1"):
    for ad, n in parca(desen):
        alt, ust, mrk = kutu(n)
        print(f"  {ad:<22} z {alt[2]:7.1f}..{ust[2]:7.1f}  x {alt[0]:6.1f}..{ust[0]:6.1f}  "
              f"y {alt[1]:6.1f}..{ust[1]:6.1f}")

print()
print("=" * 76)
print("6. TAHRIK AKSINA GORE MESAFELER  (URDF icin)")
print("=" * 76)
z_aks = teker_mrk[2]
x_mrk = (x_ler[0] + x_ler[1]) / 2.0
print(f"  referans: tahrik aksi z={z_aks:.2f}, govde orta x={x_mrk:.2f}, zemin y={zemin:.3f}")
print()
print("  bilesen                      aksa uzaklik (z)   yandan (x)   zeminden (y)")
noktalar = [
    ("catal ucu (min z)", tum_alt[2], None, None),
    ("govde z-min ucu", 696.9, None, None),
    ("govde z-max ucu", tum_ust[2], None, None),
]
for ad, z, _, _ in noktalar:
    print(f"  {ad:<28} {z - z_aks:>10.1f}")
for ad, n in sarhos:
    alt, ust, mrk = kutu(n)
    print(f"  {ad:<28} {mrk[2] - z_aks:>10.1f}   {mrk[0] - x_mrk:>10.1f}")
