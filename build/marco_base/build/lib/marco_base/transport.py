"""STM32 ile veri alisverisi icin tasima katmani.

Surucu dugumu yalnizca bu arayuze bagimlidir; gercek seri port ile sahte
donanim arasinda gecis tek bir parametreyle yapilir. Boylece navigasyon
gelistirmesi elektronik ekibinin firmware'ini beklemez.
"""

from __future__ import annotations

from typing import Protocol

import serial


class Transport(Protocol):
    """STM32 ile cift yonlu bayt akisi."""

    def write(self, data: bytes) -> None:
        """Host'tan STM32'ye bayt gonderir."""
        ...

    def read(self) -> bytes:
        """STM32'den bekleyen baytlari okur. Bloklamaz; veri yoksa b'' doner."""
        ...

    def close(self) -> None:
        """Kaynaklari serbest birakir."""
        ...


class SerialTransport:
    """Gercek UART baglantisi.

    Okuma bloklamaz: yalnizca tamponda bekleyen baytlar alinir. Bu, surucu
    dugumunun tek is parcaciginda hem okuma hem komut gonderme dongulerini
    kacirmadan surdurmesini saglar.
    """

    def __init__(self, port: str, baudrate: int, timeout: float = 0.0) -> None:
        self._serial = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        # Acilista tamponda kalmis yarim cerceveler yeniden senkron maliyeti
        # cikarmasin diye temizlenir.
        self._serial.reset_input_buffer()
        self._serial.reset_output_buffer()

    def write(self, data: bytes) -> None:
        self._serial.write(data)

    def read(self) -> bytes:
        waiting = self._serial.in_waiting
        if waiting <= 0:
            return b""
        return self._serial.read(waiting)

    def close(self) -> None:
        if self._serial.is_open:
            self._serial.close()
