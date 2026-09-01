"""Diferansiyel surus odometrisi.

Encoder tick sayaclarini robotun duzlemdeki pozuna cevirir. ROS'tan bagimsizdir.

Bu modul lokalizasyon zincirinin en alt basamagidir. Buradaki hata EKF veya AMCL
tarafindan tamamen telafi edilemez, cunku ikisi de odometriyi *goreli* hareket
kaynagi olarak kabul eder. Bu yuzden hesap olabildigince dogru yapilmalidir.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Yeni STM32 protokolunde encoder sayaci yonlu, kumulatif int32'dir.
_TICK_BITS = 32
_TICK_SPAN = 1 << _TICK_BITS
_TICK_HALF = 1 << (_TICK_BITS - 1)

# Tek örneklemede kabul edilen en büyük tick artımı.
# ~0.84 m/s × 0.5 s / 1.745 mm/tick ≈ 240; 2000 bol pay bırakır.
# Bunun üstü UART çöpü veya tek-kare bozulma sayılır.
_DEFAULT_MAX_TICK_DELTA = 2000
_DEFAULT_MAX_CONSECUTIVE_REJECTS = 3


def tick_delta(previous: int, current: int, span: int = _TICK_SPAN) -> int:
    """Iki kumulatif sayac degeri arasindaki farki tasmayi hesaba katarak dondurur.

    Varsayilan span 2^32'dir. Host int32 sarmasini en kisa isaretli fark
    olarak cozer; boylece 2147483647 -> -2147483648 gecisi kayip uretmez.
    """
    half = span >> 1
    delta = (current - previous) % span
    if delta > half:
        delta -= span
    return delta


def timestamp_delta(previous: int, current: int, bits: int = 64) -> int:
    """uint32/uint64 mikrosaniye sayaci icin isaretli fark."""
    if bits not in (32, 64):
        raise ValueError("timestamp bits yalnizca 32 veya 64 olabilir")
    span = 1 << bits
    half = span >> 1
    delta = (current - previous) % span
    if delta > half:
        delta -= span
    return delta


def wrap_ticks(value: int) -> int:
    """Sayaci C int32 araligina indirger."""
    return ((int(value) + _TICK_HALF) % _TICK_SPAN) - _TICK_HALF


@dataclass
class OdometryState:
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0
    linear_velocity: float = 0.0
    angular_velocity: float = 0.0


class DifferentialOdometry:
    """Tekerlek tick'lerinden poz ve hiz kestirimi.

    Parametreler:
        wheel_radius:       tekerlek yaricapi [m]
        wheel_separation:   tahrik tekerlerinin mil eksenleri arasi mesafe [m]
        ticks_per_rev:      firmware'in tekerin tam turunda bildirdigi yonlu tick
        max_tick_delta:     tek orneklemede kabul edilen max |Δtick|; üstü atılır
        max_consecutive_rejects:
            ardışık red sayısı; aşılınca referans yeniden alınır (STM32 reset vb.)
    """

    def __init__(
        self,
        wheel_radius: float,
        wheel_separation: float,
        ticks_per_rev: int,
        max_tick_delta: int = _DEFAULT_MAX_TICK_DELTA,
        max_consecutive_rejects: int = _DEFAULT_MAX_CONSECUTIVE_REJECTS,
    ) -> None:
        if wheel_radius <= 0.0 or wheel_separation <= 0.0 or ticks_per_rev <= 0:
            raise ValueError("wheel_radius, wheel_separation ve ticks_per_rev pozitif olmali")
        if max_tick_delta <= 0:
            raise ValueError("max_tick_delta pozitif olmali")
        if max_consecutive_rejects <= 0:
            raise ValueError("max_consecutive_rejects pozitif olmali")
        if max_tick_delta >= _TICK_HALF:
            raise ValueError(
                f"max_tick_delta {_TICK_HALF}'den kucuk olmali "
                "(int32 sarmayla karismasin)"
            )

        self.wheel_separation = wheel_separation
        self.meters_per_tick = (2.0 * math.pi * wheel_radius) / ticks_per_rev
        self.max_tick_delta = int(max_tick_delta)
        self.max_consecutive_rejects = int(max_consecutive_rejects)

        self.state = OdometryState()
        self.left_wheel_angle = 0.0
        self.right_wheel_angle = 0.0
        self._radians_per_tick = (2.0 * math.pi) / ticks_per_rev

        self._prev_ticks: tuple[int, int] | None = None
        self._prev_timestamp_us: int | None = None
        self._prev_timestamp_bits: int | None = None
        self._reject_streak = 0
        self.rejected_frames = 0

    def reset(self) -> None:
        """Pozu sifirlar ancak tick referansini korur."""
        self.state = OdometryState()

    def update(
        self,
        left_ticks: int,
        right_ticks: int,
        timestamp_us: int,
        timestamp_bits: int = 64,
    ) -> bool:
        """Yeni bir odometri cercevesi isler.

        Ilk cagri yalnizca referans alir ve False doner; poz guncellenmez.
        Sonraki cagrilar True doner. Asiri tick sicramasi filtrelenir: poz
        guncellenmez, referans korunur; ardışık red limiti dolunca referans
        yeniden alinir.
        """
        left_ticks = wrap_ticks(left_ticks)
        right_ticks = wrap_ticks(right_ticks)

        if timestamp_bits not in (32, 64):
            raise ValueError("timestamp_bits yalnizca 32 veya 64 olabilir")

        if (
            self._prev_ticks is None
            or self._prev_timestamp_us is None
            or self._prev_timestamp_bits != timestamp_bits
        ):
            self._prev_ticks = (left_ticks, right_ticks)
            self._prev_timestamp_us = timestamp_us
            self._prev_timestamp_bits = timestamp_bits
            self._reject_streak = 0
            return False

        d_left_ticks = tick_delta(self._prev_ticks[0], left_ticks)
        d_right_ticks = tick_delta(self._prev_ticks[1], right_ticks)
        dt_us = timestamp_delta(
            self._prev_timestamp_us, timestamp_us, bits=timestamp_bits
        )

        if (
            abs(d_left_ticks) > self.max_tick_delta
            or abs(d_right_ticks) > self.max_tick_delta
        ):
            self.rejected_frames += 1
            self._reject_streak += 1
            if self._reject_streak >= self.max_consecutive_rejects:
                # STM32 reset / uzun kopukluk: yeni referans al, mesafe atma.
                self._prev_ticks = (left_ticks, right_ticks)
                self._prev_timestamp_us = timestamp_us
                self._prev_timestamp_bits = timestamp_bits
                self._reject_streak = 0
            return False

        self._reject_streak = 0
        self._prev_ticks = (left_ticks, right_ticks)
        self._prev_timestamp_us = timestamp_us
        self._prev_timestamp_bits = timestamp_bits

        # Zaman geriye gitmis veya durmus: STM32 yeniden baslamis olabilir.
        # Mesafeyi yine isleriz ama hiz hesaplamayiz, cunku dt guvenilmez.
        dt = dt_us * 1e-6 if dt_us > 0 else 0.0

        d_left = d_left_ticks * self.meters_per_tick
        d_right = d_right_ticks * self.meters_per_tick

        distance = 0.5 * (d_left + d_right)
        d_theta = (d_right - d_left) / self.wheel_separation

        self._integrate(distance, d_theta)

        self.left_wheel_angle += d_left_ticks * self._radians_per_tick
        self.right_wheel_angle += d_right_ticks * self._radians_per_tick

        if dt > 0.0:
            self.state.linear_velocity = distance / dt
            self.state.angular_velocity = d_theta / dt

        return True

    def _integrate(self, distance: float, d_theta: float) -> None:
        """Poza bir hareket artimi uygular.

        Duz gidiste dogrusal, donuste tam yay (exact arc) integrasyonu kullanilir.
        Duz cizgi yaklasimi her adimda yayin kirisini alir ve donus yariçapini
        sistematik olarak buyuk gosterir; 90 derece donuslerin sik oldugu bir
        parkurda bu hata hizla birikir ve sartnamedeki 10 cm rota toleransini yer.
        """
        theta = self.state.theta

        if abs(d_theta) < 1e-9:
            self.state.x += distance * math.cos(theta)
            self.state.y += distance * math.sin(theta)
        else:
            radius = distance / d_theta
            self.state.x += radius * (math.sin(theta + d_theta) - math.sin(theta))
            self.state.y -= radius * (math.cos(theta + d_theta) - math.cos(theta))

        self.state.theta = _normalize_angle(theta + d_theta)


def _normalize_angle(angle: float) -> float:
    """Aciyi (-pi, pi] araligina indirger."""
    return math.atan2(math.sin(angle), math.cos(angle))


def wheel_speed_to_rpm(speed_m_s: float, wheel_radius: float) -> float:
    """Dogrusal teker hizini [m/s] teker devrine [RPM] cevirir."""
    if wheel_radius <= 0.0:
        raise ValueError("wheel_radius pozitif olmali")
    return speed_m_s * 60.0 / (2.0 * math.pi * wheel_radius)


def wheel_rpm_to_speed(rpm: float, wheel_radius: float) -> float:
    """Teker devrini [RPM] dogrusal teker hizina [m/s] cevirir."""
    if wheel_radius <= 0.0:
        raise ValueError("wheel_radius pozitif olmali")
    return rpm * (2.0 * math.pi * wheel_radius) / 60.0


def twist_to_wheel_speeds(
    linear: float,
    angular: float,
    wheel_separation: float,
    max_wheel_speed: float,
) -> tuple[float, float]:
    """/cmd_vel komutunu sag ve sol tekerlek hizlarina cevirir [m/s].

    Komut motorun yapabileceginin uzerindeyse iki tekerlek *ayni oranda* kirpilir.
    Tek tarafi kirpmak aracin komut edilen egriden sapmasina yol acar; oransal
    kirpma yavaslatir ama yonu korur. Rota takibi hassasiyeti icin bu tercih edilir.
    """
    half_track = 0.5 * wheel_separation
    left = linear - angular * half_track
    right = linear + angular * half_track

    peak = max(abs(left), abs(right))
    if peak > max_wheel_speed and peak > 0.0:
        scale = max_wheel_speed / peak
        left *= scale
        right *= scale

    return left, right
