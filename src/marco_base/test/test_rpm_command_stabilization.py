"""STM32'ye giden float RPM hedefi kararlastirma testleri."""

from marco_base.base_driver import stabilize_wheel_rpm


def test_microscopic_float_jitter_keeps_identical_wire_target():
    previous = (29.865503, 36.979573)
    requested = (29.865567, 36.979509)

    assert stabilize_wheel_rpm(previous, requested, 0.01) == previous


def test_meaningful_fractional_change_is_preserved():
    previous = (29.80, 36.90)
    requested = (29.85, 36.90)

    assert stabilize_wheel_rpm(previous, requested, 0.01) == requested


def test_stop_and_restart_are_immediate():
    moving = (12.25, 13.75)

    assert stabilize_wheel_rpm(moving, (0.0, 0.0), 0.01) == (0.0, 0.0)
    assert stabilize_wheel_rpm((0.0, 0.0), moving, 0.01) == moving


def test_direction_change_is_immediate():
    previous = (12.25, 13.75)
    requested = (-12.25, 13.75)

    assert stabilize_wheel_rpm(previous, requested, 0.01) == requested
