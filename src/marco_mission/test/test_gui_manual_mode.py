"""GUI manual-mode fallback policy tests."""

import pytest

from marco_mission.mission_manager import _gui_manual_mode_enabled


@pytest.mark.parametrize(
    ('mission_running', 'estop_active', 'safety_latched', 'expected'),
    (
        (False, False, False, True),
        (True, False, False, False),
        (False, True, False, False),
        (False, False, True, False),
    ),
)
def test_temporary_mode_follows_mission_and_safety_state(
    mission_running, estop_active, safety_latched, expected
):
    """Manual control lasts until autonomous execution actually starts."""
    assert _gui_manual_mode_enabled(
        hardware_manual_mode=False,
        mission_running=mission_running,
        estop_active=estop_active,
        safety_latched=safety_latched,
        temporary_fallback=True,
    ) is expected


@pytest.mark.parametrize('hardware_manual_mode', (False, True))
def test_disabling_fallback_restores_stm32_switch(hardware_manual_mode):
    """The final hardware integration needs only one parameter change."""
    assert _gui_manual_mode_enabled(
        hardware_manual_mode=hardware_manual_mode,
        mission_running=True,
        estop_active=True,
        safety_latched=True,
        temporary_fallback=False,
    ) is hardware_manual_mode
