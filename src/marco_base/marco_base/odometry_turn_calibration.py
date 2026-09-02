"""Fiziksel 360 derece donusle etkin teker araligi kalibrasyonu."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import math
import sys
import threading
import time

from nav_msgs.msg import Odometry
import rclpy
from rcl_interfaces.msg import ParameterType
from rcl_interfaces.srv import GetParameters
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node


FULL_TURN_RAD = 2.0 * math.pi
MIN_PLAUSIBLE_TURN_DEG = 180.0
MAX_PLAUSIBLE_TURN_DEG = 720.0


def normalize_angle(angle: float) -> float:
    """Aci farkini (-pi, pi] araligina getir."""
    return math.atan2(math.sin(angle), math.cos(angle))


def yaw_from_odometry(message: Odometry) -> float:
    """Odometry quaternion'undan duzlem yaw acisini dondur."""
    quaternion = message.pose.pose.orientation
    sin_yaw = 2.0 * (
        quaternion.w * quaternion.z + quaternion.x * quaternion.y
    )
    cos_yaw = 1.0 - 2.0 * (
        quaternion.y * quaternion.y + quaternion.z * quaternion.z
    )
    return math.atan2(sin_yaw, cos_yaw)


def calibrated_wheel_separation(
    current_separation: float,
    measured_turn_rad: float,
    actual_turn_rad: float = FULL_TURN_RAD,
) -> float:
    """Olculen ve gercek aciyla yeni etkin teker araligini hesapla.

    Mevcut odometri ``theta_odom = wheel_distance_difference / L_old``
    hesaplar. Ayni teker mesafesi gercekte ``theta_real`` urettigine gore:

    ``L_new = L_old * abs(theta_odom) / abs(theta_real)``
    """
    if current_separation <= 0.0:
        raise ValueError("mevcut wheel_separation pozitif olmali")
    if not math.isfinite(measured_turn_rad) or measured_turn_rad == 0.0:
        raise ValueError("olculen donus sonlu ve sifirdan farkli olmali")
    if not math.isfinite(actual_turn_rad) or actual_turn_rad == 0.0:
        raise ValueError("gercek donus sonlu ve sifirdan farkli olmali")
    return current_separation * abs(measured_turn_rad) / abs(actual_turn_rad)


@dataclass(frozen=True)
class TrialResult:
    """Tek yonlu fiziksel donus olcumu."""

    direction: str
    measured_turn_rad: float
    samples: int
    duration_s: float
    max_step_rad: float
    expected_sign_ok: bool

    @property
    def measured_degrees(self) -> float:
        """Isaretli birikimli aciyi derece dondur."""
        return math.degrees(self.measured_turn_rad)

    @property
    def magnitude_degrees(self) -> float:
        """Birikimli donusun mutlak buyuklugunu derece dondur."""
        return abs(self.measured_degrees)

    @property
    def plausible(self) -> bool:
        """Olcumun 360 derece denemesi olabilecek aralikta oldugunu bildir."""
        return (
            self.samples >= 10
            and MIN_PLAUSIBLE_TURN_DEG
            <= self.magnitude_degrees
            <= MAX_PLAUSIBLE_TURN_DEG
        )


class TurnCalibrationNode(Node):
    """Ham encoder `/odom` yaw'ini kesintisiz aciya cevirerek biriktirir."""

    def __init__(self, odom_topic: str, base_driver_node: str) -> None:
        """Odometri abonesini ve base driver parametre istemcisini kur."""
        super().__init__("odometry_turn_calibration")
        self._lock = threading.Lock()
        self._latest_yaw: float | None = None
        self._latest_message_time: float | None = None
        self._latest_frames: tuple[str, str] | None = None
        self._recording = False
        self._trial_direction = ""
        self._trial_start_time = 0.0
        self._previous_yaw: float | None = None
        self._total_yaw = 0.0
        self._sample_count = 0
        self._max_step = 0.0
        self.stop_requested = False

        driver_path = "/" + base_driver_node.strip("/")
        self._parameter_client = self.create_client(
            GetParameters,
            f"{driver_path}/get_parameters",
        )
        self.create_subscription(Odometry, odom_topic, self._on_odom, 100)

    def _on_odom(self, message: Odometry) -> None:
        yaw = yaw_from_odometry(message)
        if not math.isfinite(yaw):
            return
        now = time.monotonic()
        with self._lock:
            self._latest_yaw = yaw
            self._latest_message_time = now
            self._latest_frames = (
                message.header.frame_id,
                message.child_frame_id,
            )
            if not self._recording:
                return
            if self._previous_yaw is not None:
                step = normalize_angle(yaw - self._previous_yaw)
                self._total_yaw += step
                self._max_step = max(self._max_step, abs(step))
            self._previous_yaw = yaw
            self._sample_count += 1

    def wait_for_fresh_odom(self, timeout_s: float) -> bool:
        """Son 0.5 saniyede alinan gecerli bir ham odometri mesaji bekle."""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline and not self.stop_requested:
            with self._lock:
                received = self._latest_message_time
            if received is not None and time.monotonic() - received < 0.5:
                return True
            time.sleep(0.05)
        return False

    def odom_description(self) -> tuple[float, tuple[str, str] | None]:
        """Son yaw ve frame ciftini atomik olarak dondur."""
        with self._lock:
            if self._latest_yaw is None:
                raise RuntimeError("/odom henuz alinmadi")
            return self._latest_yaw, self._latest_frames

    def read_wheel_separation(self, timeout_s: float) -> float:
        """Calisan base driver'in etkin wheel_separation parametresini oku."""
        if not self._parameter_client.wait_for_service(timeout_sec=timeout_s):
            raise RuntimeError(
                "base driver parametre servisi bulunamadi; "
                "marco_base_driver calisiyor olmali"
            )
        request = GetParameters.Request()
        request.names = ["wheel_separation"]
        future = self._parameter_client.call_async(request)
        deadline = time.monotonic() + timeout_s
        while not future.done() and time.monotonic() < deadline:
            if self.stop_requested:
                raise RuntimeError("kullanici iptal etti")
            time.sleep(0.02)
        if not future.done():
            raise RuntimeError(
                "wheel_separation parametresi okunurken zaman asimi"
            )
        response = future.result()
        if response is None or len(response.values) != 1:
            raise RuntimeError("wheel_separation parametre cevabi gecersiz")
        value = response.values[0]
        if value.type != ParameterType.PARAMETER_DOUBLE:
            raise RuntimeError("wheel_separation parametresi double degil")
        if not math.isfinite(value.double_value) or value.double_value <= 0.0:
            raise RuntimeError(
                "wheel_separation parametresi pozitif/sonlu degil"
            )
        return value.double_value

    def begin_trial(self, direction: str) -> float:
        """Yeni bir unwrap olcumunu son ham yaw'dan baslat."""
        with self._lock:
            if self._latest_yaw is None or self._latest_message_time is None:
                raise RuntimeError("/odom hazir degil")
            if time.monotonic() - self._latest_message_time >= 0.5:
                raise RuntimeError("/odom bayat; base driver veri uretmiyor")
            self._recording = True
            self._trial_direction = direction
            self._trial_start_time = time.monotonic()
            self._previous_yaw = self._latest_yaw
            self._total_yaw = 0.0
            self._sample_count = 0
            self._max_step = 0.0
            return self._latest_yaw

    def finish_trial(self) -> TrialResult:
        """Aktif olcumu durdurup degismez sonuc dondur."""
        with self._lock:
            if not self._recording:
                raise RuntimeError("aktif donus olcumu yok")
            self._recording = False
            expected_sign = 1.0 if self._trial_direction == "left" else -1.0
            return TrialResult(
                direction=self._trial_direction,
                measured_turn_rad=self._total_yaw,
                samples=self._sample_count,
                duration_s=time.monotonic() - self._trial_start_time,
                max_step_rad=self._max_step,
                expected_sign_ok=self._total_yaw * expected_sign > 0.0,
            )


def print_trial_result(
    result: TrialResult,
    current_separation: float,
) -> float:
    """Tek yon sonucunu yazdirip onerilen etkin araligi dondur."""
    proposed = calibrated_wheel_separation(
        current_separation,
        result.measured_turn_rad,
    )
    error_percent = 100.0 * (result.magnitude_degrees / 360.0 - 1.0)
    label = "SOL" if result.direction == "left" else "SAG"
    print(f"\n{label} 360° SONUCU")
    print(f"  Odom birikimli yaw : {result.measured_degrees:+.3f}°")
    print(f"  Mutlak olculen aci: {result.magnitude_degrees:.3f}°")
    print(f"  360°'ye gore hata : {error_percent:+.3f}%")
    print(
        f"  Ornek / sure      : {result.samples} / "
        f"{result.duration_s:.2f} s"
    )
    print(f"  En buyuk yaw adimi: {math.degrees(result.max_step_rad):.3f}°")
    print(f"  Onerilen aralik   : {proposed:.6f} m")
    if not result.expected_sign_ok:
        print(
            "  UYARI: Donus isareti ROS beklentisinin tersi. "
            "Encoder yonleri kontrol edilmeden bu sonucu kullanma."
        )
    if not result.plausible:
        print(
            "  UYARI: Olculen aci 360° denemesi icin makul aralikta degil. "
            "Bu sonucu kullanma."
        )
    return proposed


def run_trial(node: TurnCalibrationNode, direction: str) -> TrialResult:
    """Kullanici kontrollu tek fiziksel donus denemesini calistir."""
    label = "SOLA" if direction == "left" else "SAGA"
    sign = "+yaw" if direction == "left" else "-yaw"
    input(
        f"\n[{label} 360°] Araci baslangic cizgisine hassas hizala, "
        "tam durdur ve ENTER'a bas..."
    )
    start_yaw = node.begin_trial(direction)
    print(f"Baslangic ham /odom yaw: {math.degrees(start_yaw):+.3f}°")
    input(
        f"Araci yerinde, yavas ve kontrollu {label} tam 360° dondur "
        f"({sign}).\n"
        "Baslangic cizgisine tekrar hassas hizalayip tamamen durunca "
        "ENTER'a bas..."
    )
    time.sleep(0.5)
    return node.finish_trial()


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    """Arac seceneklerini ROS argumanlarindan ayir."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--direction",
        choices=("both", "left", "right"),
        default="both",
        help="varsayilan: once sol, sonra sag",
    )
    parser.add_argument("--odom-topic", default="/odom")
    parser.add_argument("--base-driver-node", default="/marco_base_driver")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument(
        "--max-direction-difference-percent",
        type=float,
        default=5.0,
    )
    return parser.parse_known_args()


def main() -> None:
    """Interaktif fiziksel donus kalibrasyonunu calistir."""
    args, ros_args = parse_args()
    rclpy.init(args=ros_args)
    node = TurnCalibrationNode(args.odom_topic, args.base_driver_node)
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    spinner = threading.Thread(target=executor.spin, daemon=True)
    spinner.start()
    exit_code = 1
    try:
        print("\n=== MarCO encoder angular odometry kalibrasyonu ===")
        print(
            "Bu arac motor komutu YAYINLAMAZ; "
            "surus manuel/Bluetooth yapilir."
        )
        print("Bos alan, dusuk hiz ve hazir acil durdurma kullan.")
        print(f"Olculen kaynak: {args.odom_topic} (ham encoder odometrisi)")
        if not node.wait_for_fresh_odom(args.timeout):
            raise RuntimeError("taze /odom alinamadi; base driver'i baslat")
        separation = node.read_wheel_separation(args.timeout)
        yaw, frames = node.odom_description()
        if frames != ("odom", "base_footprint"):
            raise RuntimeError(
                f"beklenmeyen /odom frame'leri: {frames}; "
                "ham encoder odometrisi dogrulanamadi"
            )
        print(f"Mevcut wheel_separation: {separation:.6f} m")
        print(f"Ilk ham yaw             : {math.degrees(yaw):+.3f}°")

        directions = (
            ("left", "right")
            if args.direction == "both"
            else (args.direction,)
        )
        results: list[TrialResult] = []
        proposals: list[float] = []
        for direction in directions:
            result = run_trial(node, direction)
            results.append(result)
            proposals.append(print_trial_result(result, separation))

        usable = all(
            result.plausible and result.expected_sign_ok for result in results
        )
        if len(results) == 2 and usable:
            average = sum(proposals) / 2.0
            difference_percent = (
                100.0 * abs(proposals[0] - proposals[1]) / average
            )
            print("\nIKI YON KARSILASTIRMASI")
            print(f"  Sol onerisi       : {proposals[0]:.6f} m")
            print(f"  Sag onerisi       : {proposals[1]:.6f} m")
            print(f"  Yonler arasi fark : {difference_percent:.3f}%")
            if difference_percent <= args.max_direction_difference_percent:
                print(f"  ONERILEN ORTALAMA : {average:.6f} m")
                print(
                    "  Config otomatik degistirilmedi. Sonucu tekrarlayip "
                    "onayladiktan sonra base_driver.yaml'i guncelle."
                )
                exit_code = 0
            else:
                print(
                    "  UYARI: Sol/sag farki ciddi. Ortalama kullanma; mekanik "
                    "asimetri, lastik kaymasi, encoder olcek/yon farki ve "
                    "zemin tutunmasini kontrol et."
                )
        elif len(results) == 1 and usable:
            print(
                "\nTek yon sonucu hesaplandi; config degisikligi icin "
                "diger yonu da olc."
            )
            exit_code = 0
        else:
            print(
                "\nOlcum gecersiz/yon isareti hatali; "
                "config degisikligi onerilmedi."
            )
    except (EOFError, KeyboardInterrupt, RuntimeError, ValueError) as error:
        print(f"\nHATA: {error or 'kullanici iptal etti'}", flush=True)
    finally:
        executor.shutdown(timeout_sec=2.0)
        spinner.join(timeout=2.0)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
