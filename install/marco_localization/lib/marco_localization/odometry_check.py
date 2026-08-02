#!/usr/bin/env python3
"""Odometri dogrulugunu olcen ve kalibrasyon onerisi ureten manevra araci.

OLCTUGU SEY
  Odometrinin *inandigi* hareket ile robotun *gerceklestirdigi* hareket
  arasindaki fark. Bu ayrim onemli: robot komut edilen manevrayi kusursuz
  yapmasa bile odometri dogru olabilir. Tersi de gecerli. Bu araca gore
  "hata" yalnizca ikisinin arasindaki farktir.

  Gercek hareket nereden bilinir?
    Sahte donanimda  : /base/ground_truth topigi (taklit gercek pozu bilir)
    Gercek robotta   : olculemez, operator serit metre ile olcup girer

MANEVRALAR KAPALI CEVRIMDIR
  Sure hesabiyla surmek (ac cevrim) yaniltir: motor rampasi yuzunden 2 m
  komut edilen mesafe 1.9 m olur ve bu odometri hatasi sanilir. Bunun
  yerine odometri hedefe ulastigini soyleyene kadar surulur. UMBmark
  yontemi de tam olarak boyle calisir: robot odometrisine gore kareyi
  kapatir, sonra gercekte nerede oldugu olculur.

KARE TESTININ YORUMU
  Kare hem saat yonunde hem tersine surulur. Iki yondeki hata imzasi
  hangi parametrenin yanlis oldugunu ayirt eder. Rule tablosu
  `interpret` icinde, taklide bilinen hatalar enjekte edilerek deneysel
  olarak dogrulanmistir.

KULLANIM
  ros2 run marco_localization odometry_check.py --test duz
  ros2 run marco_localization odometry_check.py --test kare
  ros2 run marco_localization odometry_check.py --test hepsi
"""

from __future__ import annotations

import argparse
import math
import threading
import time

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node

COMMAND_RATE = 50.0
DISTANCE_TOLERANCE = 0.003
ANGLE_TOLERANCE = math.radians(0.3)


def normalize(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def yaw_of(msg: Odometry) -> float:
    q = msg.pose.pose.orientation
    return math.atan2(2.0 * (q.w * q.z), 1.0 - 2.0 * (q.z * q.z))


class Pose:
    """Karsilastirma icin sade poz kabi."""

    def __init__(self, x: float = 0.0, y: float = 0.0, theta: float = 0.0) -> None:
        self.x = x
        self.y = y
        self.theta = theta

    @classmethod
    def from_odometry(cls, msg: Odometry) -> "Pose":
        return cls(msg.pose.pose.position.x, msg.pose.pose.position.y, yaw_of(msg))

    def delta_to(self, other: "Pose") -> tuple[float, float, float]:
        """Bu pozdan digerine olan hareketi bu pozun govde ekseninde verir.

        Govde ekseninde vermek, odometri ile gercek pozu ayni referansa
        indirger. Ikisi dunya ekseninde farkli yerlerde olsa bile aradaki
        hareket karsilastirilabilir hale gelir.
        """
        dx = other.x - self.x
        dy = other.y - self.y
        c, s = math.cos(-self.theta), math.sin(-self.theta)
        return dx * c - dy * s, dx * s + dy * c, normalize(other.theta - self.theta)


class Maneuver:
    """Bir manevranin odometri ve gercek olcumleri."""

    def __init__(self, odom: tuple[float, float, float], truth: tuple[float, float, float] | None):
        self.odom = odom
        self.truth = truth

    @property
    def error(self) -> tuple[float, float, float] | None:
        """Gercek hareket eksi odometrinin sandigi hareket."""
        if self.truth is None:
            return None
        return tuple(t - o for t, o in zip(self.truth, self.odom))


class OdometryCheck(Node):
    """Manevra uretip odometri hatasini raporlar."""

    def __init__(self) -> None:
        super().__init__("odometry_check")
        self._cmd_pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.create_subscription(Odometry, "odom", self._on_odom, 10)
        self.create_subscription(Odometry, "base/ground_truth", self._on_truth, 10)
        self._odom: Odometry | None = None
        self._truth: Odometry | None = None

    def _on_odom(self, msg: Odometry) -> None:
        self._odom = msg

    def _on_truth(self, msg: Odometry) -> None:
        self._truth = msg

    # ------------------------------------------------------------------ altyapi

    def wait_ready(self, timeout: float = 10.0) -> bool:
        """Odometri akmaya baslayana ve komut aboneligi kurulana dek bekler.

        Abonelik kurulmadan komut yayinlamak sessiz veri kaybina yol acar;
        ilk manevranin bir kismi kaybolur ve olcum bozulur.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._odom is not None and self._cmd_pub.get_subscription_count() > 0:
                return True
            time.sleep(0.05)
        return False

    @property
    def has_ground_truth(self) -> bool:
        return self._truth is not None

    def _pose(self) -> Pose:
        return Pose.from_odometry(self._odom)

    def _truth_pose(self) -> Pose | None:
        return Pose.from_odometry(self._truth) if self._truth else None

    def _publish(self, linear: float, angular: float) -> None:
        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        self._cmd_pub.publish(msg)

    def halt(self, settle: float = 0.6) -> None:
        """Durdurur ve motor tepkisinin sonlanmasi icin bekler."""
        end = time.monotonic() + settle
        while time.monotonic() < end:
            self._publish(0.0, 0.0)
            time.sleep(1.0 / COMMAND_RATE)

    # ------------------------------------------------------------------ kapali cevrim manevralar

    # Manevralar birden fazla denemede tamamlanir. Komut sifirlandiginda arac
    # motor zaman sabiti kadar savrulur; tek geciste durmak bu savrulmayi
    # hedefe eklenmis hata olarak birakir. Dort kosede biriken yarim derece,
    # bir metrelik kenarda santimetrelerce kapanma hatasi demek. Bu yuzden her
    # manevra durdurulup savrulma olculur ve kalan pay daha yavas hizla
    # kapatilir. Boylece kapanma hatasi kontrol toleransindan degil yalnizca
    # odometriden gelir; UMBmark olcumunun gecerli olmasi buna baglidir.
    CORRECTION_ATTEMPTS = 5

    def drive_distance(self, distance: float, speed: float = 0.35) -> None:
        """Odometri hedef mesafeyi bildirene kadar, yonunu koruyarak duz surer.

        Yon koruma UMBmark yontemi icin zorunludur. Tekerlek yaricaplari
        birbirinden farkliysa odometri duz giderken kavis yaptigini sanir;
        yon duzeltmesi yapilmazsa odometrinin inandigi yol kare olmaz ve
        kapanma hatasi olcumu anlamini yitirir. Duzeltme odometriye gore
        yapildigi icin robot fiziksel olarak kavislenir. Olculmek istenen
        tam olarak bu fiziksel sapmadir.
        """
        start = self._pose()
        heading = start.theta

        for attempt in range(self.CORRECTION_ATTEMPTS):
            cap = speed if attempt == 0 else 0.08
            deadline = time.monotonic() + abs(distance) / 0.05 + 15.0

            while time.monotonic() < deadline:
                current = self._pose()
                # Yer degistirmeyi baslangic yonune izdusurmek isaretli kalan
                # pay verir; asma durumunda geri gidilerek duzeltilebilir.
                travelled = (current.x - start.x) * math.cos(heading) + (
                    current.y - start.y
                ) * math.sin(heading)
                remaining = distance - travelled
                if abs(remaining) <= DISTANCE_TOLERANCE:
                    break
                direction = 1.0 if remaining > 0.0 else -1.0
                linear = direction * min(cap, max(0.03, abs(remaining) * 1.2))
                heading_error = normalize(heading - current.theta)
                angular = max(-0.4, min(0.4, 2.0 * heading_error))
                self._publish(linear, angular)
                time.sleep(1.0 / COMMAND_RATE)

            self.halt(0.5)
            current = self._pose()
            travelled = (current.x - start.x) * math.cos(heading) + (
                current.y - start.y
            ) * math.sin(heading)
            if abs(distance - travelled) <= DISTANCE_TOLERANCE:
                break

        # Kenar sonunda kalan yon sapmasi duzeltilmezse dort kenarda birikir
        # ve odometrinin inandigi yol kapanmaz.
        residual = normalize(heading - self._pose().theta)
        if abs(residual) > ANGLE_TOLERANCE:
            self.turn_angle(residual, speed=0.15)

    def turn_angle(self, angle: float, speed: float = 0.7) -> None:
        """Odometri hedef aciya ulastigini bildirene kadar yerinde doner."""
        accumulated = 0.0
        last_yaw = self._pose().theta

        def track() -> float:
            """Sarmayi asarak birikimli aciyi guncel tutar."""
            nonlocal accumulated, last_yaw
            current_yaw = self._pose().theta
            accumulated += normalize(current_yaw - last_yaw)
            last_yaw = current_yaw
            return angle - accumulated

        for attempt in range(self.CORRECTION_ATTEMPTS):
            cap = speed if attempt == 0 else 0.10
            deadline = time.monotonic() + abs(angle) / 0.08 + 15.0

            while time.monotonic() < deadline:
                remaining = track()
                if abs(remaining) <= ANGLE_TOLERANCE:
                    break
                direction = 1.0 if remaining > 0.0 else -1.0
                self._publish(0.0, direction * min(cap, max(0.04, abs(remaining) * 1.2)))
                time.sleep(1.0 / COMMAND_RATE)

            self.halt(0.5)
            if abs(track()) <= ANGLE_TOLERANCE:
                return

    def measure(self, action) -> Maneuver:
        """Bir manevrayi calistirip odometri ve gercek hareketi olcer."""
        start_odom, start_truth = self._pose(), self._truth_pose()
        action()
        end_odom, end_truth = self._pose(), self._truth_pose()

        odom = start_odom.delta_to(end_odom)
        truth = start_truth.delta_to(end_truth) if start_truth and end_truth else None
        return Maneuver(odom, truth)


# ---------------------------------------------------------------------- raporlama


def print_maneuver(title: str, hedef: str, m: Maneuver) -> None:
    print(f"\n{title}")
    print(f"  hedef: {hedef}")
    labels = ("ileri [m]", "yan [m]", "donus [deg]")
    odom = (m.odom[0], m.odom[1], math.degrees(m.odom[2]))

    if m.error is None:
        print(f"  {'olcut':<14} {'odometri':>10}")
        for label, value in zip(labels, odom):
            print(f"  {label:<14} {value:>10.4f}")
        print("  (gercek konum referansi yok; serit metre ile olculmeli)")
        return

    truth = (m.truth[0], m.truth[1], math.degrees(m.truth[2]))
    error = (m.error[0], m.error[1], math.degrees(m.error[2]))
    print(f"  {'olcut':<14} {'odometri':>10} {'gercek':>10} {'hata':>11}")
    print(f"  {'-' * 48}")
    for label, o, t, e in zip(labels, odom, truth, error):
        print(f"  {label:<14} {o:>10.4f} {t:>10.4f} {e:>+11.4f}")


def test_straight(node: OdometryCheck, distance: float) -> None:
    m = node.measure(lambda: node.drive_distance(distance))
    print_maneuver("DUZ GIDIS", f"{distance} m ileri", m)
    if m.error:
        scale = m.truth[0] / m.odom[0] if abs(m.odom[0]) > 1e-6 else float("nan")
        print(f"  mesafe olcek katsayisi (gercek/odometri): {scale:.5f}")
        if abs(scale - 1.0) > 0.005:
            print(f"  ONERI: wheel_radius {scale:.5f} ile carpilmali")


def test_rotation(node: OdometryCheck, turns: float) -> None:
    angle = turns * 2.0 * math.pi
    m = node.measure(lambda: node.turn_angle(angle))
    print_maneuver("YERINDE DONUS", f"{turns} tur ({math.degrees(angle):.0f} deg)", m)
    if m.error:
        # Tam tur sarmalandigi icin donus bileseni yerine, gercek ile
        # odometrinin ayni sarma diliminde oldugu varsayilarak fark alinir.
        print(f"  aci hatasi: {math.degrees(m.error[2]):+.3f} deg")
        drift = math.hypot(m.truth[0], m.truth[1])
        print(f"  yerinde donuste gercek konum kaymasi: {drift * 1000:.1f} mm")


def test_square(node: OdometryCheck, side: float, clockwise: bool) -> Maneuver:
    sign = -1.0 if clockwise else 1.0

    def square() -> None:
        for _ in range(4):
            node.drive_distance(side)
            node.turn_angle(sign * math.pi / 2.0)

    m = node.measure(square)
    direction = "saat yonu" if clockwise else "saat yonu tersi"
    print_maneuver(f"KARE TESTI ({direction})", f"{side}x{side} m kapali dongu", m)

    closure_odom = math.hypot(m.odom[0], m.odom[1])
    print(f"  odometriye gore baslangica donus hatasi: {closure_odom * 1000:.1f} mm")
    if m.error:
        print(f"  GERCEK kapanma hatasi: {math.hypot(m.truth[0], m.truth[1]) * 1000:.1f} mm")
    return m


def interpret(ccw: Maneuver, cw: Maneuver) -> None:
    """Iki yonlu kare testi sonucunu kalibrasyon onerisine cevirir.

    Ayirt etme kurali tahminle degil, taklide bilinen hatalar enjekte edilip
    olculerek belirlendi:

      wheel_separation hatali (0.520 varsayilirken gercekte 0.500)
        -> aci hatasi ZIT isaretli: saat yonu tersi +14.4 deg, saat yonu
           -14.5 deg. Cunku hata yalnizca donuslerde etkir ve robot her iki
           yonde de gittigi yonde fazladan doner. Beklenen deger de bunu
           dogrular: 90 x 0.520/0.500 = 93.6 deg, dort kosede 14.4 deg fazla.

      tekerlek yaricaplari farkli (sag teker %2 farkli)
        -> aci hatasi AYNI isaretli: iki yonde de negatif. Cunku hata duz
           kisimlarda sabit bir kavis olusturur ve kavsin yonu, karenin
           hangi yonde surulduguyle degismez.

    Gercek robotta gercek konum bilinmediginden bu ayrim otomatik yapilamaz;
    o durumda olcum yontemi hatirlatilir.
    """
    print("\nDEGERLENDIRME")

    if ccw.error is None or cw.error is None:
        print("  Gercek konum referansi yok, otomatik tani yapilamaz.")
        print("  Yapilacak: her kare sonunda robotun gercek konumunu serit metre")
        print("  ile olcup odometrinin bildirdigi degerle karsilastirin.")
        return

    # Gecerlilik kosulu: UMBmark, robotun odometrisine gore baslangica
    # donmus olmasini varsayar. Odometri kendisi bile "baslangicta degilim"
    # diyorsa olcum kontrol hatasiyla kirlenmistir ve kalibrasyon cikarimi
    # yapilamaz.
    control_error = max(
        math.hypot(ccw.odom[0], ccw.odom[1]), math.hypot(cw.odom[0], cw.odom[1])
    )
    real_error = max(
        math.hypot(ccw.truth[0], ccw.truth[1]), math.hypot(cw.truth[0], cw.truth[1])
    )
    # Kontrol hatasinin sifir olmasi gerekmez; olculen sinyale gore kucuk
    # olmasi yeterlidir. Manevra toleranslari dort kenarda birikerek birkac
    # milimetre birakir, bu kacinilmazdir.
    if control_error > max(0.010, 0.25 * real_error):
        print(f"  UYARI: odometrinin kendi kapanma hatasi {control_error * 1000:.1f} mm,")
        print(f"  olculen gercek hata {real_error * 1000:.1f} mm. Kontrol hatasi olcumu")
        print("  gizleyecek kadar buyuk; kalibrasyon cikarimi atlaniyor.")
        return

    ccw_angle = math.degrees(ccw.error[2])
    cw_angle = math.degrees(cw.error[2])
    ccw_closure = math.hypot(ccw.truth[0], ccw.truth[1])
    cw_closure = math.hypot(cw.truth[0], cw.truth[1])

    print(f"  aci hatasi      saat yonu tersi: {ccw_angle:+.3f} deg")
    print(f"                  saat yonu      : {cw_angle:+.3f} deg")
    print(f"  gercek kapanma  saat yonu tersi: {ccw_closure * 1000:.1f} mm")
    print(f"                  saat yonu      : {cw_closure * 1000:.1f} mm")

    if max(ccw_closure, cw_closure) < 0.010 and max(abs(ccw_angle), abs(cw_angle)) < 0.5:
        print("\n  Odometri kabul sinirlari icinde. Kalibrasyon gerekmiyor.")
        return

    if abs(ccw_angle) > 0.3 and abs(cw_angle) > 0.3:
        if (ccw_angle > 0) != (cw_angle > 0):
            # Zit isaret: hata gidilen yonu izliyor, yani donus olceginde.
            over = ccw_angle > 0
            excess = (abs(ccw_angle) + abs(cw_angle)) / 2.0
            ratio = 1.0 + (excess if over else -excess) / 360.0
            print("\n  Aci hatasi iki yonde ZIT isaretli.")
            print("  Tani: wheel_separation degeri hatali.")
            print(
                f"  Robot odometrinin sandigindan {'fazla' if over else 'az'} donuyor, "
                f"yani gercek teker aras\u0131 mesafe varsayilandan "
                f"{'kucuk' if over else 'buyuk'}."
            )
            print(f"  Onerilen duzeltme: wheel_separation x {1.0 / ratio:.5f}")
            print("  Duzeltmeyi base_driver ve properties.xacro icinde BIRLIKTE yapin.")
            return

        # Ayni isaret: hata karenin yonunden bagimsiz, yani duz kisimlardaki
        # kavisten geliyor.
        print("\n  Aci hatasi iki yonde AYNI isaretli.")
        print("  Tani: sol ve sag tekerlegin etkin yaricaplari birbirinden farkli.")
        print("  Yapilacak: tekerlekler icin ayri olcek katsayisi tanimlanmali")
        print("  (mekanik olarak ayni tekerlekler bile lastik basinci ve yuk")
        print("  dagilimi yuzunden farkli etkin yaricapa sahip olabilir).")
        return

    print("\n  Aci hatasi kucuk ama kapanma hatasi var.")
    print("  Olasi neden: duz gidis mesafe olcegi. Once --test duz sonucuna bakin.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", default="duz", choices=["duz", "donus", "kare", "hepsi"])
    parser.add_argument("--mesafe", type=float, default=2.0, help="duz gidis mesafesi [m]")
    parser.add_argument("--kenar", type=float, default=1.0, help="kare kenar uzunlugu [m]")
    parser.add_argument("--tur", type=float, default=1.0, help="donus testi tur sayisi")
    args, ros_args = parser.parse_known_args()

    rclpy.init(args=ros_args)
    node = OdometryCheck()
    spinner = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spinner.start()

    try:
        if not node.wait_ready():
            print("HATA: /odom akmiyor veya /cmd_vel abonesi yok. base_driver calisiyor mu?")
            return

        reference = "sahte donanim gercek konumu" if node.has_ground_truth else "yok"
        print(f"gercek konum referansi: {reference}")

        if args.test in ("duz", "hepsi"):
            test_straight(node, args.mesafe)
        if args.test in ("donus", "hepsi"):
            test_rotation(node, args.tur)
        if args.test in ("kare", "hepsi"):
            ccw = test_square(node, args.kenar, clockwise=False)
            cw = test_square(node, args.kenar, clockwise=True)
            interpret(ccw, cw)
    finally:
        node.halt(0.3)
        # Once shutdown, sonra thread birlestirme: spin() ancak shutdown ile
        # geri doner. Sirasi ters olursa surec, spin icinde bekleyen thread
        # ile sonlanir ve C++ tarafinda terminate cagrilir.
        if rclpy.ok():
            rclpy.shutdown()
        spinner.join(timeout=2.0)
        node.destroy_node()


if __name__ == "__main__":
    main()
