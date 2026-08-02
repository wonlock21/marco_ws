"""STM32 firmware'inin yazilim taklidi.

Gercek karti beklemeden surucu dugumunu, odometriyi, EKF'i ve navigasyon
yiginini gelistirip test etmeyi saglar. Protokolun host tarafi degismedigi
icin firmware hazir oldugunda tek degisiklik tasima katmanini secen
parametredir.

Taklit yalnizca "calisiyormus gibi" yapmakla yetinmez; odometriyi bozan
gercek hata kaynaklarini bilincli olarak uretebilir:

  slip_factor          donuste tekerlegin bosa dondugu oran
  wheel_scale_error_*  tekerlek yaricapinin nominalden sapmasi

Bu iki mekanizma UMBmark kalibrasyonunun duzeltmeye calistigi hatalarin
tam olarak kendisidir. Varsayilan degerleri sifirdir, yani taklit dogru
davranir; hata calismasi yapilacaginda acikca acilir.

`true_pose` alani taklidin bildigi gercek konumu tutar. Odometri kestirimiyle
karsilastirildiginda Faz 3 ve Faz 5 kabul kriterleri olculebilir hale gelir.
"""

from __future__ import annotations

import math

from . import protocol as p

# Protokol §5: 200 ms komut gelmezse motorlar durur.
WATCHDOG_TIMEOUT = 0.200


class FakeStm32:
    """STM32 alt seviye kontrolcusunun davranissal modeli."""

    def __init__(
        self,
        wheel_radius: float,
        wheel_separation: float,
        ticks_per_rev: int,
        max_wheel_speed: float,
        motor_time_constant: float = 0.08,
        odometry_period: float = 0.01,
        status_period: float = 0.10,
        slip_factor: float = 0.0,
        wheel_scale_error_left: float = 0.0,
        wheel_scale_error_right: float = 0.0,
        pwm_full_scale: float = 255.0,
    ) -> None:
        self.wheel_separation = wheel_separation
        self.max_wheel_speed = max_wheel_speed
        self.pwm_full_scale = pwm_full_scale
        self.motor_time_constant = motor_time_constant
        self.odometry_period = odometry_period
        self.status_period = status_period
        self.slip_factor = slip_factor

        self._meters_per_tick = (2.0 * math.pi * wheel_radius) / ticks_per_rev
        self._scale_left = 1.0 + wheel_scale_error_left
        self._scale_right = 1.0 + wheel_scale_error_right

        self._parser = p.FrameParser()

        # Motor durumu [m/s]
        self._target_left = 0.0
        self._target_right = 0.0
        self._actual_left = 0.0
        self._actual_right = 0.0
        self._motors_enabled = False

        # Encoder birikimi. Kesirli kisim saklanir; aksi halde her adimda
        # yuvarlama kaybi olusur ve uzun surusde mesafe sistematik olarak eksilir.
        self._tick_accum_left = 0.0
        self._tick_accum_right = 0.0
        self.left_ticks = 0
        self.right_ticks = 0

        # Taklidin bildigi gercek poz (odometrinin dogrulanacagi referans)
        self.true_x = 0.0
        self.true_y = 0.0
        self.true_theta = 0.0

        self.estop_active = False
        self.manual_mode = False
        self.fault_latched = False
        self.watchdog_triggered = False
        self.command_clamped = False
        self.fork_state = 0

        self._now = 0.0
        self._started_at: float | None = None
        self._last_command_at = 0.0
        self._next_odometry_at = 0.0
        self._next_status_at = 0.0

    # ------------------------------------------------------------------ host -> stm32

    def write(self, data: bytes) -> None:
        """Host'tan gelen cerceveleri isler."""
        for msg_id, payload in self._parser.feed(data):
            self._handle(msg_id, payload)

    def _handle(self, msg_id: p.MsgId, payload: bytes) -> None:
        if msg_id is p.MsgId.CMD_WHEEL_VELOCITY:
            left_mm_s, right_mm_s, enabled = p.decode_wheel_velocity(payload)
            self._last_command_at = self._now
            self._apply_velocity_command(left_mm_s / 1000.0, right_mm_s / 1000.0, enabled)

        elif msg_id is p.MsgId.CMD_MOTOR_PWM:
            left_pwm, right_pwm, enabled = p.decode_motor_pwm(payload)
            self._last_command_at = self._now
            self._apply_pwm_command(left_pwm, right_pwm, enabled)

        elif msg_id is p.MsgId.CMD_HEARTBEAT:
            self._last_command_at = self._now

        elif msg_id is p.MsgId.CMD_SAFETY:
            command = p.decode_safety(payload)
            if command is p.SafetyCommand.SOFT_ESTOP:
                self._stop_motors()
                self.fault_latched = True
            elif command is p.SafetyCommand.CLEAR_FAULT:
                self.fault_latched = False
                self.watchdog_triggered = False

        elif msg_id is p.MsgId.CMD_FORK:
            action, _timeout_ms = p.decode_fork(payload)
            if action is p.ForkAction.UP:
                self.fork_state = 2
            elif action is p.ForkAction.DOWN:
                self.fork_state = 0

    def _apply_velocity_command(self, left: float, right: float, enabled: bool) -> None:
        clamped_left = max(-self.max_wheel_speed, min(self.max_wheel_speed, left))
        clamped_right = max(-self.max_wheel_speed, min(self.max_wheel_speed, right))
        self.command_clamped = (clamped_left != left) or (clamped_right != right)

        blocked = self.estop_active or self.fault_latched or self.watchdog_triggered
        self._motors_enabled = enabled and not blocked

        if self._motors_enabled:
            self._target_left = clamped_left
            self._target_right = clamped_right
        else:
            self._target_left = 0.0
            self._target_right = 0.0

    def _apply_pwm_command(self, left_pwm: int, right_pwm: int, enabled: bool) -> None:
        """Ham PWM komutunu acik dongu olarak uygular.

        Gercek firmware PWM'i dogrudan surucu koprusune yazar; PID devrede
        degildir. Taklit bunu PWM'i yuksuz devirle dogrusal olceklendirerek
        modeller. Dogrusallik yaklasiktir -- gercek motorda olu bolge vardir ve
        hiz yuk altinda duser -- ama acik dongunun asil zaafini dogru yansitir:
        komut ile gerceklesen hiz arasinda hicbir garanti yoktur.

        Bu yuzden PWM modunda odometri komutun teyidi degil, tek olcum
        kaynagidir; STATE_ODOMETRY yine de yayinlanir.
        """
        scale = self.max_wheel_speed / self.pwm_full_scale
        self._apply_velocity_command(left_pwm * scale, right_pwm * scale, enabled)

    def _stop_motors(self) -> None:
        self._motors_enabled = False
        self._target_left = 0.0
        self._target_right = 0.0

    # ------------------------------------------------------------------ stm32 -> host

    def update(self, now: float) -> bytes:
        """Zamani ilerletir ve host'a gonderilecek cerceveleri dondurur."""
        if self._started_at is None:
            self._started_at = now
            self._now = now
            self._last_command_at = now
            self._next_odometry_at = now
            self._next_status_at = now

        dt = now - self._now
        if dt <= 0.0:
            return b""
        self._now = now

        if now - self._last_command_at > WATCHDOG_TIMEOUT:
            if not self.watchdog_triggered:
                self.watchdog_triggered = True
            self._stop_motors()

        self._advance_motors(dt)
        self._advance_pose(dt)

        out = bytearray()
        if now >= self._next_odometry_at:
            self._next_odometry_at = self._schedule(
                self._next_odometry_at, self.odometry_period, now
            )
            out += p.encode_odometry(
                p.OdometryFrame(
                    timestamp_us=self._timestamp_us(),
                    left_ticks=self._wrap_uint16(self.left_ticks),
                    right_ticks=self._wrap_uint16(self.right_ticks),
                    left_mm_s=int(round(self._actual_left * 1000.0)),
                    right_mm_s=int(round(self._actual_right * 1000.0)),
                )
            )

        if now >= self._next_status_at:
            self._next_status_at = self._schedule(self._next_status_at, self.status_period, now)
            out += p.encode_status(
                p.StatusFrame(
                    timestamp_us=self._timestamp_us(),
                    flags=self._status_flags(),
                    battery_mv=12600,
                    current_ma_left=int(abs(self._actual_left) * 4000),
                    current_ma_right=int(abs(self._actual_right) * 4000),
                    temperature_c=32,
                    fork_state=self.fork_state,
                )
            )

        return bytes(out)

    @staticmethod
    def _schedule(previous: float, period: float, now: float) -> float:
        """Sonraki yayin zamanini kayma biriktirmeden belirler.

        `now + period` demek, cagrildigi andaki gecikmeyi her seferinde
        takvime ekler. 200 Hz'lik okuma zamanlayicisi 100 Hz'lik yayini
        ortalama 80 Hz'e dusuruyordu. Takvimi bir onceki hedefe gore
        ilerletmek gecikmeyi biriktirmez; cok geri kalinmissa takvim
        sifirlanir ki dugun birikmis yayin borcunu bir anda bosaltmasin.
        """
        following = previous + period
        return following if following > now - period else now + period

    def _advance_motors(self, dt: float) -> None:
        """Motorlarin hedef hiza birinci mertebe yaklasimini uygular.

        Ani hiz degisimi gercekci olmadigi gibi kontrolcu ayarini da yaniltir;
        raporun §7.4'unde ani hiz degisimlerinin kararliligi bozdugu kayitli.
        """
        if self.motor_time_constant <= 0.0:
            self._actual_left = self._target_left
            self._actual_right = self._target_right
            return

        alpha = 1.0 - math.exp(-dt / self.motor_time_constant)
        self._actual_left += (self._target_left - self._actual_left) * alpha
        self._actual_right += (self._target_right - self._actual_right) * alpha

    def _advance_pose(self, dt: float) -> None:
        """Gercek pozu ilerletir ve encoder tick'lerini uretir."""
        distance_left = self._actual_left * dt
        distance_right = self._actual_right * dt

        # Gercek hareket: kayma varsa donus bileseni azalir ama tekerlek doner.
        effective_left = distance_left
        effective_right = distance_right
        if self.slip_factor > 0.0:
            rotation = 0.5 * (distance_right - distance_left)
            loss = rotation * self.slip_factor
            effective_left += loss
            effective_right -= loss

        distance = 0.5 * (effective_left + effective_right)
        d_theta = (effective_right - effective_left) / self.wheel_separation

        theta = self.true_theta
        if abs(d_theta) < 1e-12:
            self.true_x += distance * math.cos(theta)
            self.true_y += distance * math.sin(theta)
        else:
            radius = distance / d_theta
            self.true_x += radius * (math.sin(theta + d_theta) - math.sin(theta))
            self.true_y -= radius * (math.cos(theta + d_theta) - math.cos(theta))
        self.true_theta = math.atan2(math.sin(theta + d_theta), math.cos(theta + d_theta))

        # Encoder tekerlegin kendi donusunu olcer, zemindeki gercek hareketi degil.
        self._tick_accum_left += (distance_left * self._scale_left) / self._meters_per_tick
        self._tick_accum_right += (distance_right * self._scale_right) / self._meters_per_tick

        whole_left = int(self._tick_accum_left)
        whole_right = int(self._tick_accum_right)
        self._tick_accum_left -= whole_left
        self._tick_accum_right -= whole_right
        self.left_ticks += whole_left
        self.right_ticks += whole_right

    def _status_flags(self) -> p.StatusFlag:
        flags = p.StatusFlag(0)
        if self.estop_active:
            flags |= p.StatusFlag.ESTOP_ACTIVE
        if self.manual_mode:
            flags |= p.StatusFlag.MODE_MANUAL
        if self._motors_enabled:
            flags |= p.StatusFlag.MOTORS_ENABLED
        if self.watchdog_triggered:
            flags |= p.StatusFlag.WATCHDOG_TRIGGERED
        if self.command_clamped:
            flags |= p.StatusFlag.CMD_CLAMPED
        if self.fork_state == 2:
            flags |= p.StatusFlag.LIMIT_SWITCH_UP
        elif self.fork_state == 0:
            flags |= p.StatusFlag.LIMIT_SWITCH_DOWN
        return flags

    def _timestamp_us(self) -> int:
        elapsed = self._now - (self._started_at or self._now)
        return int(elapsed * 1_000_000) & 0xFFFFFFFF

    @staticmethod
    def _wrap_uint16(value: int) -> int:
        """Sayaci 2^16'da sarar (0..65535); protokol ve gercek firmware ayni."""
        return value & 0xFFFF


class FakeStm32Transport:
    """FakeStm32'yi Transport arayuzune baglar."""

    def __init__(self, fake: FakeStm32, clock) -> None:
        self._fake = fake
        self._clock = clock

    def write(self, data: bytes) -> None:
        self._fake.write(data)

    def read(self) -> bytes:
        return self._fake.update(self._clock())

    def close(self) -> None:
        pass
