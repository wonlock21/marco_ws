"""odometry.py birim testleri.

Sayisal degerler elle hesaplanmistir; testin kendisi implementasyondan
bagimsiz olarak dogru olmalidir.
"""

import math

import pytest

from marco_base.odometry import (
    DifferentialOdometry,
    tick_delta,
    twist_to_wheel_speeds,
    wrap_ticks,
)

# MarCO gercek parametreleri
WHEEL_RADIUS = 0.100
WHEEL_SEPARATION = 0.460
TICKS_PER_REV = 360


def make_odom(**kwargs):
    return DifferentialOdometry(WHEEL_RADIUS, WHEEL_SEPARATION, TICKS_PER_REV, **kwargs)


def test_metre_basina_tick():
    odom = make_odom()
    # Cevre = 2*pi*0.1 = 0.6283 m, firmware'in 360 tick/tur degerine bolunur.
    assert odom.meters_per_tick == pytest.approx(0.6283185 / 360, rel=1e-6)
    assert odom.meters_per_tick == pytest.approx(0.0017453, abs=1e-7)


def test_ilk_cagri_referans_alir():
    odom = make_odom()
    assert odom.update(1000, 1000, 0) is False
    assert odom.state.x == 0.0


def test_tam_tur_bir_tekerlek_cevresi_kadar_ilerler():
    odom = make_odom()
    odom.update(0, 0, 0)
    odom.update(TICKS_PER_REV, TICKS_PER_REV, 1_000_000)

    assert odom.state.x == pytest.approx(2 * math.pi * WHEEL_RADIUS, rel=1e-6)
    assert odom.state.y == pytest.approx(0.0, abs=1e-9)
    assert odom.state.theta == pytest.approx(0.0, abs=1e-9)
    assert odom.state.linear_velocity == pytest.approx(0.6283185, rel=1e-5)


def test_yerinde_donus_ilerlemez():
    """Tekerlekler zit yonde: aci degisir, konum sabit kalir."""
    odom = make_odom()
    odom.update(0, 0, 0)
    odom.update(-TICKS_PER_REV, TICKS_PER_REV, 1_000_000)

    # d_theta = (d_right - d_left) / separation = (0.6283 - (-0.6283)) / 0.46
    beklenen = (2 * 0.6283185) / WHEEL_SEPARATION
    beklenen = math.atan2(math.sin(beklenen), math.cos(beklenen))

    assert odom.state.x == pytest.approx(0.0, abs=1e-9)
    assert odom.state.y == pytest.approx(0.0, abs=1e-9)
    assert odom.state.theta == pytest.approx(beklenen, rel=1e-6)


def test_yay_integrasyonu_duz_cizgiden_farkli():
    """Tam yay integrasyonunun duz cizgi yaklasimindan ayristigini dogrular.

    Sol teker 0.5 m, sag teker 0.6 m giderse robot bir yay cizer. Duz cizgi
    yaklasimi y'yi sifir birakirdi; dogru hesap pozitif bir y uretir.
    """
    odom = make_odom()
    mpt = odom.meters_per_tick
    left_ticks = round(0.50 / mpt)
    right_ticks = round(0.60 / mpt)

    odom.update(0, 0, 0)
    odom.update(left_ticks, right_ticks, 1_000_000)

    assert odom.state.theta > 0.0
    assert odom.state.y > 0.001
    assert odom.state.x == pytest.approx(0.5499, abs=0.005)


def test_geri_hareket():
    odom = make_odom()
    odom.update(0, 0, 0)
    odom.update(-TICKS_PER_REV, -TICKS_PER_REV, 1_000_000)

    assert odom.state.x == pytest.approx(-0.6283185, rel=1e-6)
    assert odom.state.linear_velocity < 0.0


def test_kare_parkur_baslangica_doner():
    """4 x (1 m duz + 90 derece donus) baslangic noktasina donmeli.

    Bu, Faz 3'te gercek arac uzerinde yapilacak kalibrasyon testinin
    (UMBmark) yazilim tarafindaki karsiligidir. Odometri matematigi
    kusursuzsa kapanma hatasi sifira cok yakin olmalidir.
    """
    odom = make_odom()
    mpt = odom.meters_per_tick

    left_total = 0
    right_total = 0
    t = 0
    odom.update(0, 0, t)

    duz_tick = round(1.0 / mpt)
    # 90 derece donus: d_theta = (d_r - d_l)/L, simetrik donuste d_r = -d_l
    # pi/2 = 2*d_r/L  ->  d_r = pi*L/4
    donus_tick = round((math.pi * WHEEL_SEPARATION / 4.0) / mpt)

    for _ in range(4):
        left_total += duz_tick
        right_total += duz_tick
        t += 1_000_000
        odom.update(left_total, right_total, t)

        left_total -= donus_tick
        right_total += donus_tick
        t += 1_000_000
        odom.update(left_total, right_total, t)

    kapanma_hatasi = math.hypot(odom.state.x, odom.state.y)
    assert kapanma_hatasi < 0.005, f"kapanma hatasi {kapanma_hatasi:.4f} m"


# --- Tick tasmasi (2^16) ---

def test_tick_delta_normal():
    assert tick_delta(100, 150) == 50
    assert tick_delta(150, 100) == -50


def test_tick_delta_pozitif_tasma():
    """65535 civarindan 0'a sarma: gercek fark kucuk pozitif olmali."""
    assert tick_delta(65530, 10) == 16


def test_tick_delta_negatif_tasma():
    """Geri giderken 0'dan 65535'e sarma."""
    assert tick_delta(10, 65530) == -16


def test_wrap_ticks_aralik():
    assert wrap_ticks(65536) == 0
    assert wrap_ticks(-1) == 65535
    assert wrap_ticks(70000) == 4464


def test_tasma_pozu_bozmaz():
    odom = make_odom()
    odom.update(65500, 65500, 0)
    odom.update(100, 100, 1_000_000)  # +136 tick sarma

    assert odom.state.x == pytest.approx(136 * odom.meters_per_tick, rel=1e-6)
    assert abs(odom.state.theta) < 1e-9


def test_asiri_sicrama_filtrelenir():
    """Tek karede max_tick_delta ustu fark poza yazilmamali."""
    odom = make_odom(max_tick_delta=500, max_consecutive_rejects=5)
    odom.update(0, 0, 0)
    assert odom.update(100, 100, 10_000) is True
    x_before = odom.state.x

    # UART copu: ~30000 tick sicrama
    assert odom.update(30100, 30100, 20_000) is False
    assert odom.state.x == pytest.approx(x_before)
    assert odom.rejected_frames == 1

    # Sonraki iyi ornek: onceki iyi referanstan devam (100 -> 150)
    assert odom.update(150, 150, 30_000) is True
    assert odom.state.x == pytest.approx(150 * odom.meters_per_tick, rel=1e-6)


def test_ardisik_red_referansi_yeniler():
    """STM32 reset gibi surekli uyumsuzlukta referans yeniden alinmali."""
    odom = make_odom(max_tick_delta=200, max_consecutive_rejects=3)
    odom.update(10000, 10000, 0)
    # Reset sonrasi sayaclar sifirdan
    assert odom.update(0, 0, 10_000) is False
    assert odom.update(1, 1, 20_000) is False
    assert odom.update(2, 2, 30_000) is False  # 3. red -> resync
    # Resync sonrasi kucuk artis islenmeli
    assert odom.update(50, 50, 40_000) is True
    assert odom.state.x == pytest.approx(48 * odom.meters_per_tick, rel=1e-6)


# --- Ters kinematik ---

def test_twist_duz_ileri():
    left, right = twist_to_wheel_speeds(0.5, 0.0, WHEEL_SEPARATION, 0.838)
    assert left == pytest.approx(0.5)
    assert right == pytest.approx(0.5)


def test_twist_yerinde_donus():
    left, right = twist_to_wheel_speeds(0.0, 1.0, WHEEL_SEPARATION, 0.838)
    assert left == pytest.approx(-0.23)
    assert right == pytest.approx(0.23)


def test_twist_oransal_kirpma_yonu_korur():
    """Limit asildiginda iki teker ayni oranda kirpilmali; oran korunmali."""
    left, right = twist_to_wheel_speeds(2.0, 1.0, WHEEL_SEPARATION, 0.838)

    assert max(abs(left), abs(right)) == pytest.approx(0.838)
    # Kirpma oncesi oran: (2-0.23)/(2+0.23) = 1.77/2.23
    assert left / right == pytest.approx(1.77 / 2.23, rel=1e-6)


def test_gecersiz_parametre_reddedilir():
    with pytest.raises(ValueError):
        DifferentialOdometry(0.0, WHEEL_SEPARATION, TICKS_PER_REV)
    with pytest.raises(ValueError):
        DifferentialOdometry(0.1, WHEEL_SEPARATION, 0)
    with pytest.raises(ValueError):
        DifferentialOdometry(
            0.1, WHEEL_SEPARATION, TICKS_PER_REV, max_tick_delta=40000)
