"""Diferansiyel surus odometrisi.

Encoder tick sayaclarini robotun duzlemdeki pozuna cevirir. ROS'tan bagimsizdir.

Bu modul lokalizasyon zincirinin en alt basamagidir. Buradaki hata EKF veya AMCL
tarafindan tamamen telafi edilemez, cunku ikisi de odometriyi *goreli* hareket
kaynagi olarak kabul eder. Bu yuzden hesap olabildigince dogru yapilmalidir.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Encoder sayaci 2^16'da sarar (0..65535). Kumulatif int32 yerine dar aralik
# kullanilir; float'a cevrilen ara degerlerde hassasiyet kaybi olmaz ve STM32
# sayaci sinira ulasinca sifirdan devam eder.
_TICK_SPAN = 1 << 16
_TICK_HALF = 1 << 15

# timestamp_us hâlâ uint32; tasma hesabı ayrı tutulur.
_UINT32_SPAN = 1 << 32
_UINT32_HALF = 1 << 31

# Tek örneklemede kabul edilen en büyük tick artımı.
# ~0.84 m/s × 0.5 s / 0.436 mm/tick ≈ 960; 2000 bol pay bırakır.
# Bunun üstü UART çöpü veya tek-kare bozulma sayılır.
_DEFAULT_MAX_TICK_DELTA = 2000
_DEFAULT_MAX_CONSECUTIVE_REJECTS = 3


def tick_delta(previous: int, current: int, span: int = _TICK_SPAN) -> int:
    """Iki kumulatif sayac degeri arasindaki farki tasmayi hesaba katarak dondurur.

    Varsayılan span 2^16'dır: 65535'ten sonra sayaç 0'a döner. Host tarafı
    bu sarmayı en kısa işaretli fark olarak çözer (−32768 .. 32767).
    """
    half = span >> 1
    delta = (current - previous) % span
    if delta > half:
        delta -= span
    return delta


def timestamp_delta(previous: int, current: int) -> int:
    """uint32 mikrosaniye sayaci icin isaretli fark."""
    delta = current - previous
    if delta > _UINT32_HALF:
        delta -= _UINT32_SPAN
    elif delta < -_UINT32_HALF:
        delta += _UINT32_SPAN
    return delta


def wrap_ticks(value: int) -> int:
    """Sayaci [0, 65535] araligina indirger."""
    return value & (_TICK_SPAN - 1)


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
        ticks_per_rev:      tekerlegin tam bir turunda sayilan tick (dordul dahil)
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
                "(uint16 sarmayla karismasin)"
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
    ) -> bool:
        """Yeni bir odometri cercevesi isler.

        Ilk cagri yalnizca referans alir ve False doner; poz guncellenmez.
        Sonraki cagrilar True doner. Asiri tick sicramasi filtrelenir: poz
        guncellenmez, referans korunur; ardışık red limiti dolunca referans
        yeniden alinir.
        """
        left_ticks = wrap_ticks(left_ticks)
        right_ticks = wrap_ticks(right_ticks)

        if self._prev_ticks is None or self._prev_timestamp_us is None:
            self._prev_ticks = (left_ticks, right_ticks)
            self._prev_timestamp_us = timestamp_us
            self._reject_streak = 0
            return False

        d_left_ticks = tick_delta(self._prev_ticks[0], left_ticks)
        d_right_ticks = tick_delta(self._prev_ticks[1], right_ticks)
        dt_us = timestamp_delta(self._prev_timestamp_us, timestamp_us)

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
                self._reject_streak = 0
            return False

        self._reject_streak = 0
        self._prev_ticks = (left_ticks, right_ticks)
        self._prev_timestamp_us = timestamp_us

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
