"""Orange Pi <-> STM32 UART cerceve kodlama ve cozme.

Cerceve formati docs/STM32_UART_PROTOKOL.md belgesinde tanimlidir.
Bu modul ROS'tan tamamen bagimsizdir; birim testleri dugum baslatmadan kosar.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum, IntFlag
from typing import Iterator

SYNC = b"\xAA\x55"
MAX_PAYLOAD = 64

# Cerceve: SYNC(2) + LEN(1) + MSG_ID(1) + PAYLOAD(LEN) + CRC(2)
_HEADER_LEN = 4
_CRC_LEN = 2


class MsgId(IntEnum):
    """Mesaj kimlikleri. 0x80 ve uzeri STM32'den gelen mesajlardir."""

    CMD_WHEEL_VELOCITY = 0x01
    CMD_FORK = 0x02
    CMD_SAFETY = 0x03
    CMD_MOTOR_PWM = 0x04
    CMD_HEARTBEAT = 0x05

    STATE_ODOMETRY = 0x81
    STATE_STATUS = 0x82


class StatusFlag(IntFlag):
    ESTOP_ACTIVE = 1 << 0
    MODE_MANUAL = 1 << 1
    MOTORS_ENABLED = 1 << 2
    LIMIT_SWITCH_UP = 1 << 3
    LIMIT_SWITCH_DOWN = 1 << 4
    OVERCURRENT = 1 << 5
    WATCHDOG_TRIGGERED = 1 << 6
    CMD_CLAMPED = 1 << 7
    ENCODER_FAULT = 1 << 8


class ForkAction(IntEnum):
    STOP = 0
    UP = 1
    DOWN = 2


class SafetyCommand(IntEnum):
    NORMAL = 0
    SOFT_ESTOP = 1
    CLEAR_FAULT = 2


# Payload yapilari. '<' hizalama dolgusunu kapatir; STM32 tarafiyla bayt bayt uyumlu.
_FMT_WHEEL_VELOCITY = "<hhB"   # left_mm_s, right_mm_s, flags
_FMT_MOTOR_PWM = "<hhB"        # left_pwm, right_pwm, flags
_FMT_FORK = "<BH"              # action, timeout_ms
_FMT_SAFETY = "<B"             # command
_FMT_ODOMETRY = "<Iiihh"       # timestamp_us, left_ticks, right_ticks, left_mm_s, right_mm_s
_FMT_STATUS = "<IHHhhbB"       # timestamp_us, flags, battery_mv, cur_l, cur_r, temp_c, fork_state

ODOMETRY_PAYLOAD_LEN = struct.calcsize(_FMT_ODOMETRY)  # 16
STATUS_PAYLOAD_LEN = struct.calcsize(_FMT_STATUS)      # 14


def crc16_ccitt(data: bytes) -> int:
    """CRC16/CCITT-FALSE: poly 0x1021, init 0xFFFF, ters cevirme yok.

    Tablosuz bit bit hesaplanir. 16 baytlik cercevelerde 100 Hz'de maliyeti
    ihmal edilebilir; tablo optimizasyonu gereksiz karmasiklik olurdu.
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def encode(msg_id: MsgId, payload: bytes = b"") -> bytes:
    """Tam cerceveyi olusturur."""
    if len(payload) > MAX_PAYLOAD:
        raise ValueError(f"payload {len(payload)} bayt, en fazla {MAX_PAYLOAD}")
    body = bytes([len(payload), int(msg_id)]) + payload
    return SYNC + body + struct.pack("<H", crc16_ccitt(body))


# --- Komut kodlayicilari (Orange Pi -> STM32) ---

def encode_wheel_velocity(left_mm_s: int, right_mm_s: int, enabled: bool) -> bytes:
    return encode(
        MsgId.CMD_WHEEL_VELOCITY,
        struct.pack(_FMT_WHEEL_VELOCITY, int(left_mm_s), int(right_mm_s), 1 if enabled else 0),
    )


def encode_motor_pwm(left_pwm: int, right_pwm: int, enabled: bool) -> bytes:
    """Ham PWM komutu. STM32 PID'i devreye almaz, degeri surucuye dogrudan yazar.

    Alan tipi int16: bugun host tarafi 0..150 arasi gonderiyor ama isaret geri
    yonu, genislik ise ileride 0..255 veya 0..1000'e cikilmasini protokolu
    degistirmeden mumkun kilar. Kablo formati sabit kaldigi surece aralik
    degisikligi yalnizca bir parametre degisikligidir.
    """
    return encode(
        MsgId.CMD_MOTOR_PWM,
        struct.pack(_FMT_MOTOR_PWM, int(left_pwm), int(right_pwm), 1 if enabled else 0),
    )


def encode_fork(action: ForkAction, timeout_ms: int) -> bytes:
    return encode(MsgId.CMD_FORK, struct.pack(_FMT_FORK, int(action), int(timeout_ms)))


def encode_safety(command: SafetyCommand) -> bytes:
    return encode(MsgId.CMD_SAFETY, struct.pack(_FMT_SAFETY, int(command)))


def encode_heartbeat() -> bytes:
    return encode(MsgId.CMD_HEARTBEAT)


# --- Durum mesajlari (STM32 -> Orange Pi) ---

@dataclass(frozen=True)
class OdometryFrame:
    timestamp_us: int
    left_ticks: int
    right_ticks: int
    left_mm_s: int
    right_mm_s: int


@dataclass(frozen=True)
class StatusFrame:
    timestamp_us: int
    flags: StatusFlag
    battery_mv: int
    current_ma_left: int
    current_ma_right: int
    temperature_c: int
    fork_state: int


def encode_odometry(f: OdometryFrame) -> bytes:
    """Yalnizca sahte STM32 ve testler icin; gercek firmware bunu C'de uretir.

    Tick alanlari kabloda int32 kalir ama deger her zaman [0, 65535] araligindadir
    (2^16 sarma). Host decode sirasinda da maskeler.
    """
    return encode(
        MsgId.STATE_ODOMETRY,
        struct.pack(
            _FMT_ODOMETRY,
            f.timestamp_us & 0xFFFFFFFF,
            f.left_ticks & 0xFFFF,
            f.right_ticks & 0xFFFF,
            f.left_mm_s,
            f.right_mm_s,
        ),
    )


def encode_status(f: StatusFrame) -> bytes:
    return encode(
        MsgId.STATE_STATUS,
        struct.pack(
            _FMT_STATUS,
            f.timestamp_us & 0xFFFFFFFF,
            int(f.flags),
            f.battery_mv,
            f.current_ma_left,
            f.current_ma_right,
            f.temperature_c,
            f.fork_state,
        ),
    )


def decode_wheel_velocity(payload: bytes) -> tuple[int, int, bool]:
    """(left_mm_s, right_mm_s, enabled) dondurur."""
    left, right, flags = struct.unpack(_FMT_WHEEL_VELOCITY, payload)
    return left, right, bool(flags & 1)


def decode_motor_pwm(payload: bytes) -> tuple[int, int, bool]:
    """(left_pwm, right_pwm, enabled) dondurur."""
    left, right, flags = struct.unpack(_FMT_MOTOR_PWM, payload)
    return left, right, bool(flags & 1)


def decode_fork(payload: bytes) -> tuple[ForkAction, int]:
    action, timeout_ms = struct.unpack(_FMT_FORK, payload)
    return ForkAction(action), timeout_ms


def decode_safety(payload: bytes) -> SafetyCommand:
    (command,) = struct.unpack(_FMT_SAFETY, payload)
    return SafetyCommand(command)


def decode_odometry(payload: bytes) -> OdometryFrame:
    """STATE_ODOMETRY cozer.

    Kanonik boyut 16 bayttir. Sahadaki firmware bazen 24 bayt gonderiyor
    (ilk 16 protokolle ayni, sondaki 8 sifir/padding); bu durumda ilk 16
    bayt kullanilir. 16'dan kisa paket reddedilir.
    """
    if len(payload) < ODOMETRY_PAYLOAD_LEN:
        raise ValueError(
            f"odometry payload {len(payload)} bayt, en az {ODOMETRY_PAYLOAD_LEN} gerekli"
        )
    ts, left, right, left_mm_s, right_mm_s = struct.unpack_from(
        _FMT_ODOMETRY, payload
    )
    return OdometryFrame(
        ts,
        left & 0xFFFF,
        right & 0xFFFF,
        left_mm_s,
        right_mm_s,
    )


def decode_status(payload: bytes) -> StatusFrame:
    ts, flags, batt, cl, cr, temp, fork = struct.unpack(_FMT_STATUS, payload)
    return StatusFrame(ts, StatusFlag(flags), batt, cl, cr, temp, fork)


class FrameParser:
    """Akis tabanli cerceve cozucu.

    UART'tan gelen veri parca parca okunur; bir cerceve iki okuma arasinda
    bolunebilir. Bu sinif ic tampon tutar ve tam cerceveleri tesbit ettikce verir.

    Bozuk CRC veya gecersiz uzunluk durumunda tek bayt ileri kayarak yeniden
    senkronlanir. Boylece hatali bir bayt tum akisi kalici olarak bozmaz.
    """

    def __init__(self) -> None:
        self._buf = bytearray()
        self.crc_errors = 0
        self.resyncs = 0

    def feed(self, data: bytes) -> Iterator[tuple[MsgId, bytes]]:
        self._buf.extend(data)

        while True:
            start = self._buf.find(SYNC)
            if start < 0:
                # Senkron yok. Yarim kalmis bir SYNC olabilecegi icin son bayti sakla.
                if len(self._buf) > 1:
                    del self._buf[:-1]
                return

            if start > 0:
                del self._buf[:start]
                self.resyncs += 1

            if len(self._buf) < _HEADER_LEN:
                return

            length = self._buf[2]
            if length > MAX_PAYLOAD:
                del self._buf[:2]
                self.resyncs += 1
                continue

            total = _HEADER_LEN + length + _CRC_LEN
            if len(self._buf) < total:
                return

            body = bytes(self._buf[2:_HEADER_LEN + length])
            (received_crc,) = struct.unpack_from("<H", self._buf, _HEADER_LEN + length)

            if received_crc != crc16_ccitt(body):
                self.crc_errors += 1
                del self._buf[:2]
                continue

            msg_id_raw = self._buf[3]
            payload = bytes(self._buf[_HEADER_LEN:_HEADER_LEN + length])
            del self._buf[:total]

            try:
                yield MsgId(msg_id_raw), payload
            except ValueError:
                # Tanimsiz mesaj kimligi. Cerceve gecerliydi, sadece bilmiyoruz;
                # ileri surum uyumlulugu icin sessizce atlanir.
                continue
