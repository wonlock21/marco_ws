"""Launch policy checks for production-only PLC assignment auto-start."""

from pathlib import Path


SOURCE_ROOT = Path(__file__).parents[2]


def test_mission_launch_declares_safe_disabled_default():
    text = (SOURCE_ROOT / 'marco_mission/launch/mission.launch.py').read_text(
        encoding='utf-8')

    assert "'plc_auto_start', default_value='false'" in text
    assert "'plc_auto_start': LaunchConfiguration('plc_auto_start')" in text


def test_real_system_enables_only_real_backend_auto_start():
    text = (
        SOURCE_ROOT / 'marco_bringup/launch/real_system.launch.py'
    ).read_text(encoding='utf-8')

    assert '"task_source": "mock_plc" if fake else "plc"' in text
    assert '"plc_backend": "mock" if fake else "real"' in text
    assert '"plc_auto_start": "false" if fake else "true"' in text
