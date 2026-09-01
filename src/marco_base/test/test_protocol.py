"""protocol.py birim testleri."""

import struct

import pytest

from marco_base import protocol as p


def test_crc_bilinen_deger():
    # CRC16/CCITT-FALSE referans vektoru
    assert p.crc16_ccitt(b"123456789") == 0x29B1


def test_cerceve_gidis_donus():
    frame = p.encode_wheel_rpm(80, -80, True)
    parser = p.FrameParser()
    messages = list(parser.feed(frame))
    assert len(messages) == 1
    msg_id, payload = messages[0]
    assert msg_id is p.MsgId.CMD_WHEEL_RPM
    assert payload == frame[4:-2]
    assert p.decode_wheel_rpm(payload) == (80, -80, True)
    assert parser.crc_errors == 0


def test_bolunmus_cerceve_birlestirilir():
    """UART okumasi cerceveyi ortadan bolerse veri kaybedilmemeli."""
    frame = p.encode_odometry(p.OdometryFrame(1_000_000, 1440, 1440, 100, 100))
    parser = p.FrameParser()

    assert list(parser.feed(frame[:5])) == []
    messages = list(parser.feed(frame[5:]))

    assert len(messages) == 1
    odom = p.decode_odometry(messages[0][1])
    assert odom.left_ticks == 1440
    assert odom.timestamp_us == 1_000_000


def test_bozuk_crc_atilir_ve_sonraki_cerceve_okunur():
    good = p.encode_status(
        p.StatusFrame(5, p.StatusFlag.MOTORS_ENABLED, 12600, 1000, 1010, 31, 0)
    )
    corrupt = bytearray(good)
    corrupt[-1] ^= 0xFF

    parser = p.FrameParser()
    messages = list(parser.feed(bytes(corrupt) + good))

    assert len(messages) == 1
    assert parser.crc_errors == 1
    status = p.decode_status(messages[0][1])
    assert status.battery_mv == 12600
    assert p.StatusFlag.MOTORS_ENABLED in status.flags


def test_cop_baytlari_sonrasi_yeniden_senkron():
    frame = p.encode_heartbeat()
    parser = p.FrameParser()
    messages = list(parser.feed(b"\x00\x11\xAA\x22" + frame))

    assert len(messages) == 1
    assert messages[0][0] is p.MsgId.CMD_HEARTBEAT
    assert parser.resyncs >= 1


def test_ardisik_cerceveler_tek_okumada():
    stream = p.encode_heartbeat() + p.encode_safety(p.SafetyCommand.CLEAR_FAULT)
    parser = p.FrameParser()
    messages = list(parser.feed(stream))

    assert [m[0] for m in messages] == [p.MsgId.CMD_HEARTBEAT, p.MsgId.CMD_SAFETY]


def test_tick_int32_isaretini_korur():
    """Yonlu int32 tick degerleri 16 bite daraltilmamalidir."""
    frame = p.encode_odometry(p.OdometryFrame(99, -5000, -4999, -200, -199))
    parser = p.FrameParser()
    odom = p.decode_odometry(list(parser.feed(frame))[0][1])

    assert odom.left_ticks == -5000
    assert odom.right_ticks == -4999
    assert odom.right_mm_s == -199


def test_tick_65536_degeri_korunur():
    frame = p.encode_odometry(p.OdometryFrame(1, 65535, 65536, 0, 0))
    parser = p.FrameParser()
    odom = p.decode_odometry(list(parser.feed(frame))[0][1])
    assert odom.left_ticks == 65535
    assert odom.right_ticks == 65536


def test_odometri_24_bayt_geriye_uyumlu():
    """Sahadaki paket: uint64 zaman + encoder/hiz + float32 IMU."""
    payload = struct.pack("<Qiihhf", 176_664, 100, 200, 10, -10, 37.5)
    odom = p.decode_odometry(payload)
    assert odom.timestamp_us == 176664
    assert odom.left_ticks == 100
    assert odom.right_ticks == 200
    assert odom.left_mm_s == 10
    assert odom.right_mm_s == -10
    assert odom.imu_yaw_deg == pytest.approx(37.5)
    assert odom.timestamp_bits == 64


def test_odometri_20_bayt_uint64_zaman_imu_yok():
    """Imu'suz ara surumde ilk 20 bayt aynen korunur."""
    payload = struct.pack("<Qiihh", 250_000, 123, 456, 70, 71)
    odom = p.decode_odometry(payload)
    assert odom.timestamp_us == 250_000
    assert odom.left_ticks == 123
    assert odom.right_ticks == 456
    assert odom.imu_yaw_deg is None
    assert odom.timestamp_bits == 64


def test_odometri_20_bayt_int32_tick_degerini_korur():
    payload = struct.pack("<Qiihh", 250_000, 70_000, -80_000, 70, -71)
    odom = p.decode_odometry(payload)
    assert odom.left_ticks == 70_000
    assert odom.right_ticks == -80_000
    assert odom.imu_yaw_deg is None
    assert odom.timestamp_bits == 64


def test_sahadan_alinan_24_baytlik_odometri_cozulur():
    payload = bytes.fromhex(
        "e8b21586000000007d04000054fcffff00000000646fdd42"
    )
    odom = p.decode_odometry(payload)
    assert odom.timestamp_us == 2_249_569_000
    assert odom.left_ticks == 1_149
    assert odom.right_ticks == -940
    assert odom.left_mm_s == 0
    assert odom.right_mm_s == 0
    assert odom.imu_yaw_deg == pytest.approx(110.71756, rel=1e-5)


def test_odometri_16_bayt_legacy_imu_yok():
    payload = struct.pack("<Iiihh", 100, 1, 2, 3, 4)
    odom = p.decode_odometry(payload)
    assert odom.imu_yaw_deg is None
    assert odom.timestamp_bits == 32


def test_odometri_kisa_payload_red():
    with pytest.raises(ValueError):
        p.decode_odometry(bytes(15))


def test_odometri_bilinmeyen_boyut_red():
    with pytest.raises(ValueError):
        p.decode_odometry(bytes(21))


def test_status_bayraklari():
    flags = p.StatusFlag.ESTOP_ACTIVE | p.StatusFlag.MODE_MANUAL
    frame = p.encode_status(p.StatusFrame(1, flags, 12000, 0, 0, 25, 3))
    parser = p.FrameParser()
    status = p.decode_status(list(parser.feed(frame))[0][1])

    assert p.StatusFlag.ESTOP_ACTIVE in status.flags
    assert p.StatusFlag.MODE_MANUAL in status.flags
    assert p.StatusFlag.OVERCURRENT not in status.flags


def test_rpm_komutu_motorlari_kapatabilir():
    payload = p.encode_wheel_rpm(10, 10, False)[4:-2]
    assert p.decode_wheel_rpm(payload) == (10, 10, False)
