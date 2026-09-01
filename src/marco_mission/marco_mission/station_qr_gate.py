"""State-gated, single-use station QR matching."""

from __future__ import annotations

from dataclasses import dataclass
import math
import time


@dataclass(frozen=True)
class QrGateResult:
    """Result of one QR observation."""

    accepted: bool
    reason: str


class StationQrGate:
    """Accept only the expected QR during one station approach session."""

    IDLE = "IDLE"
    APPROACHING = "APPROACHING_STATION"
    VERIFIED = "QR_VERIFIED"
    TURNING = "TURNING_180"
    LINE_FOLLOW_READY = "LINE_FOLLOW_READY"
    LINE_FOLLOW_DOCKING = "LINE_FOLLOW_DOCKING"
    PICKUP_READY = "PICKUP_READY"
    DROPOFF_READY = "DROPOFF_READY"
    EXITING = "EXITING_STATION"

    def __init__(
        self, max_age_s: float = 0.75, debounce_s: float = 0.15
    ) -> None:
        if max_age_s <= 0.0 or debounce_s < 0.0:
            raise ValueError("QR freshness/debounce limits are invalid")
        self.max_age_s = float(max_age_s)
        self.debounce_s = float(debounce_s)
        self.phase = self.IDLE
        self.target_station = ""
        self.expected_qr_id = ""
        self.last_reject_reason = ""
        self._last_value = ""
        self._last_observation = -math.inf

    @property
    def armed(self) -> bool:
        """Return whether this session can still accept a QR."""
        return self.phase == self.APPROACHING

    def arm(self, target_station: str, expected_qr_id: str) -> None:
        """Start a fresh approach session."""
        station = str(target_station).strip()
        qr_id = str(expected_qr_id).strip()
        if not station or not qr_id:
            raise ValueError("target_station and expected_qr_id are required")
        self.target_station = station
        self.expected_qr_id = qr_id
        self.last_reject_reason = ""
        self.phase = self.APPROACHING

    def observe(
        self,
        qr_id: str,
        valid: bool,
        age_s: float | None = 0.0,
        now: float | None = None,
    ) -> QrGateResult:
        """Validate one observation without allowing a repeated trigger."""
        value = str(qr_id).strip()
        if self.phase != self.APPROACHING:
            return self._reject("qr_trigger_not_armed")
        if not valid or not value:
            return self._reject("invalid_qr")
        if age_s is None or not math.isfinite(age_s) or age_s > self.max_age_s:
            return self._reject("stale_qr")
        observed = time.monotonic() if now is None else float(now)
        if (
            value == self._last_value
            and observed - self._last_observation < self.debounce_s
        ):
            return self._reject("qr_debounce")
        self._last_value = value
        self._last_observation = observed
        if value != self.expected_qr_id:
            return self._reject("unexpected_qr")
        self.phase = self.VERIFIED
        self.last_reject_reason = ""
        self._last_value = ""
        self._last_observation = -math.inf
        return QrGateResult(True, "accepted")

    def exiting(self) -> None:
        """Disarm the trigger while leaving the station."""
        self.phase = self.EXITING

    def turning(self) -> None:
        """Enter the maneuver phase after a verified QR."""
        if self.phase != self.VERIFIED:
            raise ValueError("turning requires a verified station QR")
        self.phase = self.TURNING

    def line_follow_ready(self) -> None:
        """Mark successful turn and atomic readiness for docking control."""
        if self.phase != self.TURNING:
            raise ValueError("line-follow handoff requires an active turn")
        self.phase = self.LINE_FOLLOW_READY

    def docking(self) -> None:
        """Consume the QR trigger when timed reverse control starts."""
        if self.phase != self.LINE_FOLLOW_READY:
            raise RuntimeError("docking requires LINE_FOLLOW_READY")
        self.phase = self.LINE_FOLLOW_DOCKING

    def docking_complete(self, pickup: bool) -> None:
        """Expose the lift-ready state only after a verified stop."""
        if self.phase != self.LINE_FOLLOW_DOCKING:
            raise RuntimeError("completion requires LINE_FOLLOW_DOCKING")
        self.phase = self.PICKUP_READY if pickup else self.DROPOFF_READY

    def reset(self) -> None:
        """Clear all session state."""
        self.phase = self.IDLE
        self.target_station = ""
        self.expected_qr_id = ""
        self.last_reject_reason = ""
        self._last_value = ""
        self._last_observation = -math.inf

    def _reject(self, reason: str) -> QrGateResult:
        self.last_reject_reason = reason
        return QrGateResult(False, reason)
