#!/usr/bin/env python3
"""Orange Pi GPIO uzerinden darbeli aktif buzzer surucusu."""

import shutil
import subprocess
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool
from std_srvs.srv import SetBool


class BuzzerDriver(Node):
    """SetBool komutunu 400 ms acik / 250 ms kapali desene cevirir."""

    def __init__(self) -> None:
        super().__init__("buzzer_driver")
        self.declare_parameter("wpi_pin", 2)
        self.declare_parameter("active_high", True)
        self.declare_parameter("on_time_s", 0.40)
        self.declare_parameter("off_time_s", 0.25)
        self.declare_parameter("gpio_command", "gpio")
        self.declare_parameter("dry_run", False)

        self._pin = int(self.get_parameter("wpi_pin").value)
        self._active_high = bool(self.get_parameter("active_high").value)
        self._on_time = float(self.get_parameter("on_time_s").value)
        self._off_time = float(self.get_parameter("off_time_s").value)
        self._gpio_command = str(self.get_parameter("gpio_command").value)
        self._dry_run = bool(self.get_parameter("dry_run").value)
        if self._pin < 0:
            raise ValueError("wpi_pin negatif olamaz")
        if self._on_time <= 0.0 or self._off_time <= 0.0:
            raise ValueError("on_time_s ve off_time_s sifirdan buyuk olmali")

        self._enabled = False
        self._output_on = False
        self._next_transition = 0.0

        state_qos = QoSProfile(depth=1)
        state_qos.reliability = ReliabilityPolicy.RELIABLE
        state_qos.durability = DurabilityPolicy.TRANSIENT_LOCAL
        self._state_pub = self.create_publisher(Bool, "/buzzer/state", state_qos)
        self._service = self.create_service(
            SetBool, "/buzzer/set_enabled", self._set_enabled
        )

        self._initialize_gpio()
        self._publish_state()
        self._timer = self.create_timer(0.02, self._tick)
        self.get_logger().info(
            "Buzzer hazir | fiziksel pin=7 GPIO1_D6 wPi=%d | "
            "desen=%.0f ms acik / %.0f ms kapali%s"
            % (
                self._pin,
                self._on_time * 1000.0,
                self._off_time * 1000.0,
                " | DRY-RUN" if self._dry_run else "",
            )
        )

    def _run_gpio(self, *arguments: str) -> None:
        if self._dry_run:
            return
        try:
            result = subprocess.run(
                [self._gpio_command, *arguments],
                check=False,
                capture_output=True,
                text=True,
                timeout=2.0,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RuntimeError(f"GPIO komutu calistirilamadi: {error}") from error
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise RuntimeError(
                f"GPIO komutu basarisiz ({result.returncode}): {detail}"
            )

    def _initialize_gpio(self) -> None:
        if not self._dry_run and shutil.which(self._gpio_command) is None:
            raise RuntimeError(f"GPIO komutu bulunamadi: {self._gpio_command}")
        self._run_gpio("mode", str(self._pin), "out")
        self._write_output(False)

    def _write_output(self, enabled: bool) -> None:
        level = enabled if self._active_high else not enabled
        self._run_gpio("write", str(self._pin), "1" if level else "0")
        self._output_on = enabled

    def _publish_state(self) -> None:
        message = Bool()
        message.data = self._enabled
        self._state_pub.publish(message)

    def _set_enabled(self, request, response):
        requested = bool(request.data)
        try:
            if requested:
                if not self._enabled:
                    self._enabled = True
                    self._write_output(True)
                    self._next_transition = time.monotonic() + self._on_time
            else:
                self._enabled = False
                self._write_output(False)
            self._publish_state()
            response.success = True
            response.message = "buzzer acik" if self._enabled else "buzzer kapali"
        except RuntimeError as error:
            self._enabled = False
            try:
                self._write_output(False)
            except RuntimeError:
                pass
            self._publish_state()
            response.success = False
            response.message = str(error)
            self.get_logger().error(str(error))
        return response

    def _tick(self) -> None:
        if not self._enabled or time.monotonic() < self._next_transition:
            return
        try:
            if self._output_on:
                self._write_output(False)
                self._next_transition = time.monotonic() + self._off_time
            else:
                self._write_output(True)
                self._next_transition = time.monotonic() + self._on_time
        except RuntimeError as error:
            self._enabled = False
            self.get_logger().error(f"Buzzer guvenli kapatildi: {error}")
            try:
                self._write_output(False)
            except RuntimeError:
                pass
            self._publish_state()

    def destroy_node(self) -> bool:
        self._enabled = False
        try:
            self._write_output(False)
        except RuntimeError as error:
            self.get_logger().error(f"Buzzer kapanisinda GPIO LOW yapilamadi: {error}")
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None
    try:
        node = BuzzerDriver()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except (RuntimeError, ValueError) as error:
        if node is not None:
            node.get_logger().fatal(str(error))
        else:
            print(f"buzzer_driver: {error}")
        raise
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
