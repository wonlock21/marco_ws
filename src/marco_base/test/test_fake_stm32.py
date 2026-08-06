"""Sahte STM32 davranis testleri.

En onemli test `test_odometri_sahte_donanimi_izler`: sahte donanimin urettigi
tick'ler odometri modulune verildiginde, odometrinin kestirdigi poz sahte
donanimin bildigi gercek poza yakinsamalidir. Bu test iki modulun (protokol
uretimi ve odometri cozumu) birbirinin tersi oldugunu dogrular; biri
degistirilirse digeri uyumsuz kalirsa test duser.
"""

import math

from marco_base import protocol as p
from marco_base.fake_stm32 import WATCHDOG_TIMEOUT, FakeStm32
from marco_base.odometry import DifferentialOdometry

WHEEL_RADIUS = 0.100
WHEEL_SEPARATION = 0.460
TICKS_PER_REV = 360
MAX_WHEEL_SPEED = 0.838

COMMAND_PERIOD = 0.02
STEP = 0.005


def make_fake(**kwargs) -> FakeStm32:
    params = dict(
        wheel_radius=WHEEL_RADIUS,
        wheel_separation=WHEEL_SEPARATION,
        ticks_per_rev=TICKS_PER_REV,
        max_wheel_speed=MAX_WHEEL_SPEED,
    )
    params.update(kwargs)
    return FakeStm32(**params)


def command(fake: FakeStm32, left: float, right: float, enabled: bool = True) -> None:
    fake.write(
        p.encode_wheel_velocity(
            left_mm_s=int(round(left * 1000)),
            right_mm_s=int(round(right * 1000)),
            enabled=enabled,
        )
    )


def run(fake: FakeStm32, left: float, right: float, duration: float, start: float = 0.0):
    """Sabit hiz komutuyla belirtilen sure boyunca cevirir; cerceveleri dondurur."""
    frames = bytearray()
    now = start
    next_command = start
    end = start + duration
    while now < end:
        if now >= next_command:
            command(fake, left, right)
            next_command = now + COMMAND_PERIOD
        frames += fake.update(now)
        now += STEP
    return bytes(frames), now


def decode_all(data: bytes):
    parser = p.FrameParser()
    return list(parser.feed(data))


def test_komut_gelmeden_hareket_yok():
    fake = make_fake()
    for i in range(50):
        fake.update(i * STEP)
    assert fake.left_ticks == 0
    assert fake.right_ticks == 0


def test_ileri_komut_tick_uretir():
    fake = make_fake()
    run(fake, 0.3, 0.3, 2.0)
    assert fake.left_ticks > 0
    assert fake.right_ticks > 0
    # Sag ve sol ayni komutu aldi; tick sayilari birbirine cok yakin olmali.
    assert abs(fake.left_ticks - fake.right_ticks) <= 1


METERS_PER_TICK = (2 * math.pi * WHEEL_RADIUS) / TICKS_PER_REV
MOTOR_TIME_CONSTANT = 0.08


def coast_distance(fake: FakeStm32, start_ticks: int) -> float:
    return (fake.left_ticks - start_ticks) * METERS_PER_TICK


def test_watchdog_komut_kesilince_durdurur():
    fake = make_fake()
    speed = 0.4
    _, now = run(fake, speed, speed, 1.0)
    ticks_before = fake.left_ticks

    # Komut gondermeyi birak, yalnizca zamani ilerlet.
    end = now + WATCHDOG_TIMEOUT + 1.0
    while now < end:
        fake.update(now)
        now += STEP

    assert fake.watchdog_triggered

    # Beklenen durma mesafesi iki bilesenden olusur: watchdog suresi boyunca
    # sabit hizda gidilen yol, arti motor zaman sabiti kadar savrulma.
    expected = speed * WATCHDOG_TIMEOUT + speed * MOTOR_TIME_CONSTANT
    assert abs(coast_distance(fake, ticks_before) - expected) < 0.02

    frozen = fake.left_ticks
    for _ in range(100):
        fake.update(now)
        now += STEP
    assert fake.left_ticks == frozen


def test_haberlesme_kesintisi_durma_mesafesi_butcesi():
    """Haberlesme kesildiginde alinan yolu kayda gecirir.

    Bu bir dogruluk testi degil, tasarim butcesinin kilidi. Sartname arac
    guzergahtan 10 cm'den fazla sapmamasini istiyor. En yuksek hizda
    haberlesme kesilirse arac watchdog suresi boyunca kor gider; bu mesafe
    guvenlik bolgesi boyutlarini belirler. Deger buyurse test duser ve
    watchdog suresinin kisaltilmasi gundeme gelir.
    """
    fake = make_fake()
    _, now = run(fake, MAX_WHEEL_SPEED, MAX_WHEEL_SPEED, 2.0)
    ticks_before = fake.left_ticks

    end = now + WATCHDOG_TIMEOUT + 1.0
    while now < end:
        fake.update(now)
        now += STEP

    stopping_distance = coast_distance(fake, ticks_before)
    # 200 ms watchdog + 80 ms motor sabiti, 0.838 m/s'de yaklasik 23 cm.
    assert stopping_distance < 0.25, (
        f"durma mesafesi {stopping_distance * 100:.1f} cm; "
        "watchdog suresi kisaltilmali"
    )


def test_watchdog_sonrasi_komut_temizlenmeden_calismaz():
    """Watchdog attiktan sonra yalnizca komut gondermek yetmez.

    Guvenlik acisindan onemli: haberlesme kesilip geri geldiginde arac
    kendiliginden hareket etmemeli, once hata acikca temizlenmeli.
    """
    fake = make_fake()
    _, now = run(fake, 0.4, 0.4, 0.5)
    end = now + WATCHDOG_TIMEOUT + 0.5
    while now < end:
        fake.update(now)
        now += STEP
    assert fake.watchdog_triggered

    _, now = run(fake, 0.4, 0.4, 0.5, start=now)
    ticks_after_retry = fake.left_ticks

    fake.write(p.encode_safety(p.SafetyCommand.CLEAR_FAULT))
    assert not fake.watchdog_triggered
    run(fake, 0.4, 0.4, 1.0, start=now)
    assert fake.left_ticks > ticks_after_retry


def test_hiz_siniri_asilinca_bayrak_kalkar():
    fake = make_fake()
    command(fake, MAX_WHEEL_SPEED * 2, MAX_WHEEL_SPEED * 2)
    fake.update(0.0)
    fake.update(STEP)
    assert fake.command_clamped
    frames = decode_all(fake.update(STEP * 2) + fake.update(0.2))
    status = [p.decode_status(payload) for mid, payload in frames if mid is p.MsgId.STATE_STATUS]
    assert status, "durum cercevesi yayinlanmadi"
    assert p.StatusFlag.CMD_CLAMPED in status[-1].flags


def test_estop_hareketi_engeller():
    fake = make_fake()
    fake.estop_active = True
    run(fake, 0.4, 0.4, 1.0)
    assert fake.left_ticks == 0


def test_yerinde_donus_tickleri_zit_isaretli():
    fake = make_fake()
    speed = 0.3
    run(fake, -speed, speed, 2.0)
    assert fake.left_ticks < 0
    assert fake.right_ticks > 0
    assert fake.true_theta > 0.0
    # Yerinde donuste merkez kaymamali.
    assert math.hypot(fake.true_x, fake.true_y) < 1e-6


def test_odometri_sahte_donanimi_izler():
    """Sahte donanimin tickleri odometriye verildiginde gercek poz cikmali."""
    fake = make_fake()
    odometry = DifferentialOdometry(
        wheel_radius=WHEEL_RADIUS,
        wheel_separation=WHEEL_SEPARATION,
        ticks_per_rev=TICKS_PER_REV,
    )

    # Duz git, sonra kavis ciz: iki hareket tipi de sinanmis olur.
    data, now = run(fake, 0.3, 0.3, 3.0)
    more, _ = run(fake, 0.20, 0.35, 4.0, start=now)

    for msg_id, payload in decode_all(data + more):
        if msg_id is p.MsgId.STATE_ODOMETRY:
            frame = p.decode_odometry(payload)
            odometry.update(frame.left_ticks, frame.right_ticks, frame.timestamp_us)

    state = odometry.state
    assert math.hypot(state.x - fake.true_x, state.y - fake.true_y) < 0.005
    assert abs(state.theta - fake.true_theta) < math.radians(0.5)


def test_tekerlek_olcek_hatasi_odometriyi_saptirir():
    """Enjekte edilen yaricap hatasi odometri ile gercegi ayirmali.

    Kalibrasyon aracinin olctugu sinyalin gercekten var oldugunu dogrular;
    hata enjeksiyonu calismazsa arac hicbir seyi saptamayacagi icin sessizce
    "sorun yok" derdi.
    """
    fake = make_fake(wheel_scale_error_right=0.02)
    odometry = DifferentialOdometry(
        wheel_radius=WHEEL_RADIUS,
        wheel_separation=WHEEL_SEPARATION,
        ticks_per_rev=TICKS_PER_REV,
    )
    data, _ = run(fake, 0.3, 0.3, 5.0)
    for msg_id, payload in decode_all(data):
        if msg_id is p.MsgId.STATE_ODOMETRY:
            frame = p.decode_odometry(payload)
            odometry.update(frame.left_ticks, frame.right_ticks, frame.timestamp_us)

    # Gercekte duz gitti, odometri saga/sola kavis yaptigini sanmali.
    assert abs(fake.true_theta) < 1e-6
    assert abs(odometry.state.theta) > math.radians(1.0)


def test_tick_sayaci_kesirli_hareketi_biriktirir():
    """Tek adimda bir tick'ten az hareket kaybolmamali.

    Yuvarlama her adimda asagi yapilirsa uzun surusde mesafe sistematik
    olarak eksik cikar. 100 Hz'de yavas hizda bu kayip belirgindir.
    """
    fake = make_fake()
    slow = 0.02
    duration = 10.0
    run(fake, slow, slow, duration)

    meters_per_tick = (2 * math.pi * WHEEL_RADIUS) / TICKS_PER_REV
    measured = fake.left_ticks * meters_per_tick
    # Motor rampasi nedeniyle beklenenden bir miktar az olacak ama
    # yuvarlama kaybi olsaydi fark cok daha buyuk olurdu.
    assert measured > slow * duration * 0.95


def test_catal_komutu_durum_bildirir():
    fake = make_fake()
    fake.write(p.encode_fork(p.ForkAction.UP, timeout_ms=3000))
    fake.update(0.0)
    frames = decode_all(fake.update(0.2))
    status = [p.decode_status(payload) for mid, payload in frames if mid is p.MsgId.STATE_STATUS]
    assert status[-1].fork_state == 2
    assert p.StatusFlag.LIMIT_SWITCH_UP in status[-1].flags


def test_pwm_komutu_tick_uretir():
    """Acik dongu PWM yolu da motoru hareket ettirmeli."""
    fake = make_fake(pwm_full_scale=255.0)
    now = 0.0
    next_command = 0.0
    end = 2.0
    while now < end:
        if now >= next_command:
            # 150/255 * 0.838 ≈ 0.49 m/s hedef
            fake.write(p.encode_motor_pwm(150, 150, True))
            next_command = now + COMMAND_PERIOD
        fake.update(now)
        now += STEP

    assert fake.left_ticks > 0
    assert abs(fake.left_ticks - fake.right_ticks) <= 1
