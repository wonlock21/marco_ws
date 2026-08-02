"""protocol.py birim testleri."""

import struct

import pytest

from marco_base import protocol as p


def test_crc_bilinen_deger():
    # CRC16/CCITT-FALSE referans vektoru
    assert p.crc16_ccitt(b"123456789") == 0x29B1


def test_cerceve_gidis_donus():
    frame = p.encode_wheel_velocity(500, -500, True)
    parser = p.FrameParser()
    messages = list(parser.feed(frame))
    assert len(messages) == 1
    msg_id, payload = messages[0]
    assert msg_id is p.MsgId.CMD_WHEEL_VELOCITY
    assert payload == frame[4:-2]
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


def test_tick_uint16_sarma():
    """Tick alanlari 2^16'da sarar; negatif ham deger maskelenir."""
    frame = p.encode_odometry(p.OdometryFrame(99, -5000, -4999, -200, -199))
    parser = p.FrameParser()
    odom = p.decode_odometry(list(parser.feed(frame))[0][1])

    assert odom.left_ticks == (-5000 & 0xFFFF)
    assert odom.right_ticks == (-4999 & 0xFFFF)
    assert odom.right_mm_s == -199


def test_tick_ust_sinir_sifira_doner():
    frame = p.encode_odometry(p.OdometryFrame(1, 65535, 65536, 0, 0))
    parser = p.FrameParser()
    odom = p.decode_odometry(list(parser.feed(frame))[0][1])
    assert odom.left_ticks == 65535
    assert odom.right_ticks == 0


def test_odometri_24_bayt_geriye_uyumlu():
    """Sahadaki firmware 24 bayt gonderiyor; ilk 16 protokol alanidir."""
    core = struct.pack("<Iiihh", 176664, 100, 200, 10, -10)
    payload = core + bytes(8)
    odom = p.decode_odometry(payload)
    assert odom.timestamp_us == 176664
    assert odom.left_ticks == 100
    assert odom.right_ticks == 200
    assert odom.left_mm_s == 10
    assert odom.right_mm_s == -10


def test_odometri_kisa_payload_red():
    with pytest.raises(ValueError):
        p.decode_odometry(bytes(15))


def test_status_bayraklari():
    flags = p.StatusFlag.ESTOP_ACTIVE | p.StatusFlag.MODE_MANUAL
    frame = p.encode_status(p.StatusFrame(1, flags, 12000, 0, 0, 25, 3))
    parser = p.FrameParser()
    status = p.decode_status(list(parser.feed(frame))[0][1])

    assert p.StatusFlag.ESTOP_ACTIVE in status.flags
    assert p.StatusFlag.MODE_MANUAL in status.flags
    assert p.StatusFlag.OVERCURRENT not in status.flags


def test_motor_pwm_gidis_donus():
    frame = p.encode_motor_pwm(104, 96, True)
    parser = p.FrameParser()
    messages = list(parser.feed(frame))

    assert len(messages) == 1
    msg_id, payload = messages[0]
    assert msg_id is p.MsgId.CMD_MOTOR_PWM
    assert p.decode_motor_pwm(payload) == (104, 96, True)


def test_motor_pwm_negatif_yon():
    """Geri surus isaretli PWM ile ifade edilir."""
    left, right, enabled = p.decode_motor_pwm(
        p.encode_motor_pwm(-40, -40, True)[4:-2]
    )
    assert left == -40
    assert right == -40
    assert enabled is True
