"""Tests for exclusive mock/real PLC backend selection."""

import pytest

from marco_plc.launch_selection import select_plc_backend


@pytest.mark.parametrize(
    ('backend', 'source', 'expected_backend', 'expected_source'),
    (
        ('mock', 'plc', 'mock', 'mock_plc'),
        ('real', 'mock_plc', 'real', 'plc'),
        ('auto', 'mock_plc', 'mock', 'mock_plc'),
        ('auto', 'plc', 'real', 'plc'),
    ),
)
def test_backend_selection_starts_exactly_one_provider(
    backend, source, expected_backend, expected_source
):
    """Resolve one provider and force the matching mission source label."""
    selection = select_plc_backend(backend, source)
    assert selection.backend == expected_backend
    assert selection.task_source == expected_source
    assert selection.start_mock != selection.start_real


@pytest.mark.parametrize('backend', ('', 'both', 'modbus_tcp'))
def test_invalid_backend_is_rejected(backend):
    """Reject selections that could make provider ownership ambiguous."""
    with pytest.raises(ValueError):
        select_plc_backend(backend, 'plc')
