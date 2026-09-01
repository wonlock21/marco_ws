"""Tests for target/state/QR guarded station approach triggers."""

from marco_mission.station_qr_gate import StationQrGate


def test_expected_qr_is_accepted_once_per_approach():
    gate = StationQrGate()
    gate.arm("A1", "q2")

    assert not gate.observe("q3", True).accepted
    assert gate.armed
    assert gate.observe("q2", True).accepted
    assert gate.phase == StationQrGate.VERIFIED
    assert not gate.observe("q2", True).accepted


def test_exit_and_new_station_rearm_are_explicit():
    gate = StationQrGate()
    gate.arm("B2", "q8")
    assert gate.observe("q8", True).accepted
    gate.exiting()
    assert not gate.observe("q8", True).accepted

    gate.arm("A1", "q2")
    assert gate.target_station == "A1"
    assert gate.expected_qr_id == "q2"
    assert gate.observe("q2", True).accepted


def test_verified_qr_can_advance_to_turn_and_handoff_once():
    gate = StationQrGate()
    gate.arm("B1", "q9")
    assert gate.observe("q9", True).accepted
    gate.turning()
    assert gate.phase == StationQrGate.TURNING
    assert not gate.observe("q9", True).accepted
    gate.line_follow_ready()
    assert gate.phase == StationQrGate.LINE_FOLLOW_READY
    gate.docking()
    assert gate.phase == StationQrGate.LINE_FOLLOW_DOCKING
    gate.docking_complete(pickup=True)
    assert gate.phase == StationQrGate.PICKUP_READY
    gate.exiting()
    assert gate.phase == StationQrGate.EXITING


def test_invalid_detection_never_triggers():
    gate = StationQrGate()
    gate.arm("A2", "q3")
    result = gate.observe("q3", False)
    assert not result.accepted
    assert result.reason == "invalid_qr"
    assert gate.armed


def test_stale_and_debounced_qr_do_not_trigger():
    gate = StationQrGate(max_age_s=0.5, debounce_s=0.2)
    gate.arm("A3", "q4")
    assert gate.observe("q4", True, age_s=0.6, now=1.0).reason == "stale_qr"
    assert gate.observe(
        "wrong", True, age_s=0.0, now=2.0).reason == "unexpected_qr"
    assert gate.observe(
        "wrong", True, age_s=0.0, now=2.1).reason == "qr_debounce"
    assert gate.observe("q4", True, age_s=0.0, now=2.2).accepted
