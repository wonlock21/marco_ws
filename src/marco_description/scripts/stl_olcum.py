"""SolidWorks montajindan ihrac edilen STL parcalarini olculendirir.

Parcalar montaj koordinat sisteminde ihrac edildigi icin her parcanin sinir
kutusu aracin icindeki gercek konumunu verir. URDF olculeri bu ciktidan
turetilir; tahmin edilen degerler yerine olculen degerler kullanilir.

Kullanim:
    python3 stl_olcum.py <klasor>
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


def uclari_oku(yol: Path) -> np.ndarray:
    """Binary STL dosyasindan ucgen kose noktalarini (N, 3) olarak dondurur.

    Binary STL duzeni: 80 bayt baslik, uint32 ucgen sayisi, ardindan her
    ucgen icin 12 float32 (normal + 3 kose) ve 2 bayt oznitelik.
    """
    ham = yol.read_bytes()
    sayi = int(np.frombuffer(ham, dtype="<u4", count=1, offset=80)[0])
    kayit = np.dtype(
        [("normal", "<f4", 3), ("koseler", "<f4", (3, 3)), ("oznitelik", "<u2")]
    )
    veri = np.frombuffer(ham, dtype=kayit, count=sayi, offset=84)
    return veri["koseler"].reshape(-1, 3)


def main() -> int:
    klasor = Path(sys.argv[1])
    kayitlar = []

    for yol in sorted(klasor.glob("*.STL")):
        try:
            noktalar = uclari_oku(yol)
        except (ValueError, OSError) as hata:
            print(f"ATLANDI {yol.name}: {hata}", file=sys.stderr)
            continue

        alt = noktalar.min(axis=0)
        ust = noktalar.max(axis=0)
        kayitlar.append(
            {
                "ad": yol.name.replace("GenelMontaj - ", "").replace(".STL", ""),
                "alt": alt,
                "ust": ust,
                "olcu": ust - alt,
                "merkez": (alt + ust) / 2.0,
                "ucgen": len(noktalar) // 3,
            }
        )

    if not kayitlar:
        print("parca bulunamadi", file=sys.stderr)
        return 1

    tum_alt = np.min([k["alt"] for k in kayitlar], axis=0)
    tum_ust = np.max([k["ust"] for k in kayitlar], axis=0)

    print("=" * 108)
    print(f"{len(kayitlar)} parca | toplam ucgen: {sum(k['ucgen'] for k in kayitlar):,}")
    print("=" * 108)
    print("MONTAJIN TAMAMI (STL birimi):")
    print(f"  alt kose : {tum_alt}")
    print(f"  ust kose : {tum_ust}")
    print(f"  olcu     : {tum_ust - tum_alt}")
    print("=" * 108)
    print(
        f"{'parca':<52}{'olcu (x,y,z)':>26}{'merkez (x,y,z)':>26}{'ucgen':>8}"
    )
    print("-" * 108)

    for k in sorted(kayitlar, key=lambda r: -float(np.prod(r["olcu"]))):
        olcu = "  ".join(f"{v:7.1f}" for v in k["olcu"])
        merkez = "  ".join(f"{v:7.1f}" for v in k["merkez"])
        print(f"{k['ad'][:51]:<52}{olcu:>26}{merkez:>26}{k['ucgen']:>8}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
