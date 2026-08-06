"""Serit takibinden gelen ham PWM degerlerini STM32'ye tasiyan koprü dugumu.

  /pwm_left, /pwm_right  ->  kirpma -> CMD_MOTOR_PWM  ->  UART
  UART (STATE_STATUS)    ->  /base/estop, /base/manual_mode, /base/battery
  UART (STATE_ODOMETRY)  ->  /base/wheel_speed_left, /base/wheel_speed_right

base_driver.py ILE AYNI ANDA CALISTIRILAMAZ. Ikisi de ayni seri porta yazar;
cerceveler ic ice gecer ve STM32 ikisini de CRC hatasi olarak atar. Bunlar iki
ayri kontrol yolu:

  base_driver  kapali dongu -- mm/s hedefi gonderir, PID'i STM32 kosturur
  pwm_bridge   acik dongu   -- ham PWM gonderir, PID devrede degildir

Acik dongunun bedeli encoder geri beslemesinin devre disi kalmasidir: ayni PWM
egimde daha yavas, bosta daha hizli surer ve iki motor arasindaki uretim
farki arac hafifce yana kaymasina yol acar. Serit takibi bu sapmayi kameradan
gelen hatayla kapattigi icin serit surusunde tolere edilebilir; seridin
olmadigi yerde (Nav2 ile nokta hedefine gitmek gibi) tolere edilemez.

Odometri bu dugum tarafindan YAYINLANMAZ. STM32 tick gondermeye devam eder
ama pozun cozumu base_driver'in isidir; ikisinin ayni /odom topigini
yayinlamasi tekrar eden kod ve celisen kaynak anlamina gelirdi. Bu dugum
yalnizca STM32'nin olctugu tekerlek hizlarini yayinlar -- PWM ile gerceklesen
hiz arasindaki iliskiyi kalibre etmek icin gereken sey tam olarak budur.
"""

from __future__ import annotations

import struct

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles
from sensor_msgs.msg import BatteryState
from std_msgs.msg import Bool, Float32

from . import protocol as p
from .fake_stm32 import FakeStm32, FakeStm32Transport
from .transport import SerialTransport

HEARTBEAT_PERIOD = 0.1

# Kirpma uyarisi bu aralikta en fazla bir kez basilir. 50 Hz'de kirpma
# suruyorsa saniyede 50 satir log akar ve gercek hatalar gorunmez olur.
CLAMP_WARN_PERIOD = 2.0


class PwmBridge(Node):
    """PWM komutlarini STM32'ye ileten acik dongu koprusu."""

    def __init__(self) -> None:
        super().__init__("marco_pwm_bridge")

        self._declare_parameters()

        self.pwm_min = float(self.get_parameter("pwm_min").value)
        self.pwm_max = float(self.get_parameter("pwm_max").value)
        self.pwm_timeout = float(self.get_parameter("pwm_timeout").value)

        if self.pwm_max <= self.pwm_min:
            raise ValueError(
                f"pwm_max ({self.pwm_max}) pwm_min'den ({self.pwm_min}) buyuk olmali"
            )

        self._transport = self._create_transport()
        self._parser = p.FrameParser()

        # Iki kanal ayri mesajlarla gelir, dolayisiyla tazelikleri de ayri
        # izlenir. Bkz. _send_command.
        self._left_pwm = 0.0
        self._right_pwm = 0.0
        self._left_stamp: float | None = None
        self._right_stamp: float | None = None

        self._status: p.StatusFrame | None = None
        self._last_heartbeat = 0.0
        self._last_clamp_warn = 0.0
        self._was_stale = True

        qos = QoSPresetProfiles.SENSOR_DATA.value
        self._estop_pub = self.create_publisher(Bool, "base/estop", 10)
        self._manual_pub = self.create_publisher(Bool, "base/manual_mode", 10)
        self._battery_pub = self.create_publisher(BatteryState, "base/battery", qos)
        self._speed_left_pub = self.create_publisher(Float32, "base/wheel_speed_left", qos)
        self._speed_right_pub = self.create_publisher(Float32, "base/wheel_speed_right", qos)

        self.create_subscription(Float32, "pwm_left", self._on_left_pwm, 10)
        self.create_subscription(Float32, "pwm_right", self._on_right_pwm, 10)

        command_rate = float(self.get_parameter("command_rate").value)
        read_rate = float(self.get_parameter("read_rate").value)
        self.create_timer(1.0 / command_rate, self._send_command)
        self.create_timer(1.0 / read_rate, self._read_transport)

        # Acilis dizisi (protokol §6): varsa kilitli hatayi temizle.
        self._transport.write(p.encode_safety(p.SafetyCommand.CLEAR_FAULT))

        source = (
            "SAHTE DONANIM"
            if self.get_parameter("use_fake_hardware").value
            else self.get_parameter("serial_port").value
        )
        self.get_logger().info(
            f"marco_pwm_bridge hazir | {source} | acik dongu (PID yok) | "
            f"PWM araligi {self.pwm_min:.0f}..{self.pwm_max:.0f} | "
            f"{command_rate:.0f} Hz komut | zaman asimi {self.pwm_timeout:.2f} s"
        )

    # ------------------------------------------------------------------ kurulum

    def _declare_parameters(self) -> None:
        self.declare_parameter("serial_port", "/dev/marco_stm32")
        self.declare_parameter("baudrate", 115200)
        self.declare_parameter("use_fake_hardware", False)

        # Kabul edilen PWM araligi. lane_tracking/controller.py bugun 0..150
        # uretiyor; bu sinirlar oradaki kirpmanin tekrari degil, bagimsiz
        # dogrulamasidir. Kontrolcu kazanci degistiginde tasan degerlerin
        # motora ulasmasi engellenir.
        self.declare_parameter("pwm_min", 0.0)
        self.declare_parameter("pwm_max", 150.0)

        self.declare_parameter("command_rate", 50.0)
        self.declare_parameter("read_rate", 200.0)
        # Kamera goruntusu kesilirse arac durur. STM32 watchdog'u (200 ms) son
        # savunma hatti; bu deger normal isleyisteki ilk hat.
        self.declare_parameter("pwm_timeout", 0.5)

        # Sahte donanim yalnizca use_fake_hardware=true iken kurulur. Asagidaki
        # dort deger taklidin fizik modeli icindir, gercek donanimda kullanilmaz.
        self.declare_parameter("wheel_radius", 0.100)
        self.declare_parameter("wheel_separation", 0.460)
        self.declare_parameter("ticks_per_revolution", 360)
        self.declare_parameter("max_wheel_speed", 0.838)
        # Tam gaza karsilik gelen PWM. Firmware'in timer ARR degeri ile ayni
        # olmalidir; taklit PWM'i hiza cevirirken bunu olcek olarak kullanir.
        self.declare_parameter("pwm_full_scale", 255.0)

    def _create_transport(self):
        if self.get_parameter("use_fake_hardware").value:
            self.fake = FakeStm32(
                wheel_radius=self.get_parameter("wheel_radius").value,
                wheel_separation=self.get_parameter("wheel_separation").value,
                ticks_per_rev=self.get_parameter("ticks_per_revolution").value,
                max_wheel_speed=self.get_parameter("max_wheel_speed").value,
                pwm_full_scale=float(self.get_parameter("pwm_full_scale").value),
            )
            return FakeStm32Transport(self.fake, self._now_seconds)

        self.fake = None
        return SerialTransport(
            port=self.get_parameter("serial_port").value,
            baudrate=self.get_parameter("baudrate").value,
        )

    def _now_seconds(self) -> float:
        return self.get_clock().now().nanoseconds * 1e-9

    # ------------------------------------------------------------------ komut yolu

    def _on_left_pwm(self, msg: Float32) -> None:
        self._left_pwm = float(msg.data)
        self._left_stamp = self._now_seconds()

    def _on_right_pwm(self, msg: Float32) -> None:
        self._right_pwm = float(msg.data)
        self._right_stamp = self._now_seconds()

    def _send_command(self) -> None:
        """Sabit hizda cerceve gonderir.

        Komut, mesaj geldiginde degil zamanlayicida gonderilir. Ucu birden
        gerekce:

        1. Sol ve sag PWM iki ayri mesajdir. Mesaj basina gonderilseydi
           sol guncellenip sag guncellenmemis bir ara durum kabloya cikardi
           ve arac her karede kisa sureli yanlis yone kirardi.
        2. Kamera hizi degisken (isik kosuluna gore kare atlanir); STM32'nin
           watchdog'u ise sabit periyot bekler. Zamanlayici ikisini ayirir.
        3. PWM ayni kalsa bile cerceve akmaya devam eder, boylece watchdog
           yalnizca gercek bir kesintide tetiklenir.
        """
        now = self._now_seconds()

        if self._is_stale(now):
            left, right = 0.0, 0.0
            if not self._was_stale:
                self.get_logger().warn(
                    f"PWM komutu {self.pwm_timeout:.2f} s'dir gelmiyor, motorlar durduruluyor"
                )
                self._was_stale = True
        else:
            left, right = self._clamp(self._left_pwm, self._right_pwm, now)
            if self._was_stale:
                self.get_logger().info("PWM komutu akiyor, motorlar serbest")
                self._was_stale = False

        blocked = self._status is not None and (
            p.StatusFlag.ESTOP_ACTIVE in self._status.flags
            or p.StatusFlag.MODE_MANUAL in self._status.flags
        )

        self._transport.write(
            p.encode_motor_pwm(
                left_pwm=int(round(left)),
                right_pwm=int(round(right)),
                enabled=not blocked,
            )
        )

        if now - self._last_heartbeat >= HEARTBEAT_PERIOD:
            self._last_heartbeat = now
            self._transport.write(p.encode_heartbeat())

    def _is_stale(self, now: float) -> bool:
        """Iki kanaldan HERHANGI biri eskimisse komut gecersizdir.

        Yalnizca eskiyen kanali sifirlamak daha yumusak gorunur ama tehlikeli
        olur: sag PWM donarken sol 0'a duserse arac tam gaz yerinde donmeye
        baslar. Bir kanali kaybetmek yon bilgisini tamamen kaybetmek demektir,
        bu yuzden ikisi birlikte sifirlanir.
        """
        for stamp in (self._left_stamp, self._right_stamp):
            if stamp is None or now - stamp > self.pwm_timeout:
                return True
        return False

    def _clamp(self, left: float, right: float, now: float) -> tuple[float, float]:
        clamped_left = max(self.pwm_min, min(self.pwm_max, left))
        clamped_right = max(self.pwm_min, min(self.pwm_max, right))

        if (clamped_left != left or clamped_right != right) and (
            now - self._last_clamp_warn >= CLAMP_WARN_PERIOD
        ):
            self._last_clamp_warn = now
            self.get_logger().warn(
                f"PWM kirpildi: sol {left:.1f}->{clamped_left:.1f} "
                f"sag {right:.1f}->{clamped_right:.1f} "
                f"(sinir {self.pwm_min:.0f}..{self.pwm_max:.0f})"
            )

        return clamped_left, clamped_right

    # ------------------------------------------------------------------ okuma yolu

    def _read_transport(self) -> None:
        try:
            data = self._transport.read()
        except OSError as exc:
            self.get_logger().error(f"seri port okuma hatasi: {exc}")
            return

        if not data:
            return

        for msg_id, payload in self._parser.feed(data):
            try:
                if msg_id is p.MsgId.STATE_STATUS:
                    self._on_status(p.decode_status(payload))
                elif msg_id is p.MsgId.STATE_ODOMETRY:
                    self._on_odometry(p.decode_odometry(payload))
            except (struct.error, ValueError) as exc:
                self.get_logger().warn(
                    f"protokol uyumsuzlugu msg=0x{int(msg_id):02X} "
                    f"len={len(payload)}: {exc} | payload={payload[:32].hex()}"
                )

    def _on_odometry(self, frame: p.OdometryFrame) -> None:
        self._speed_left_pub.publish(Float32(data=frame.left_mm_s / 1000.0))
        self._speed_right_pub.publish(Float32(data=frame.right_mm_s / 1000.0))

    def _on_status(self, frame: p.StatusFrame) -> None:
        previous = self._status
        self._status = frame

        if previous is None or previous.flags != frame.flags:
            self._log_flag_changes(previous, frame)

        self._estop_pub.publish(Bool(data=p.StatusFlag.ESTOP_ACTIVE in frame.flags))
        self._manual_pub.publish(Bool(data=p.StatusFlag.MODE_MANUAL in frame.flags))

        battery = BatteryState()
        battery.header.stamp = self.get_clock().now().to_msg()
        battery.voltage = frame.battery_mv / 1000.0
        battery.current = -(frame.current_ma_left + frame.current_ma_right) / 1000.0
        battery.temperature = float(frame.temperature_c)
        battery.present = True
        self._battery_pub.publish(battery)

    def _log_flag_changes(self, previous: p.StatusFrame | None, current: p.StatusFrame) -> None:
        old = previous.flags if previous else p.StatusFlag(0)
        for flag, message in (
            (p.StatusFlag.ESTOP_ACTIVE, "ACIL STOP"),
            (p.StatusFlag.MODE_MANUAL, "MANUEL MOD"),
            (p.StatusFlag.OVERCURRENT, "ASIRI AKIM"),
            (p.StatusFlag.WATCHDOG_TRIGGERED, "WATCHDOG"),
            (p.StatusFlag.ENCODER_FAULT, "ENCODER HATASI"),
            (p.StatusFlag.CMD_CLAMPED, "STM32 KOMUTU KIRPTI"),
        ):
            if flag in current.flags and flag not in old:
                self.get_logger().warn(f"{message} aktif")
            elif flag not in current.flags and flag in old:
                self.get_logger().info(f"{message} temizlendi")

    def destroy_node(self) -> bool:
        try:
            self._transport.write(p.encode_motor_pwm(0, 0, False))
            self._transport.close()
        except OSError:
            pass
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = PwmBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
