"""Flake8 lint entry point."""

from ament_flake8.main import main_with_errors
import pytest


@pytest.mark.flake8
@pytest.mark.linter
def test_flake8():
    """Check package Python style."""
    rc, errors = main_with_errors(argv=[])
    assert rc == 0, 'Found %d errors:\n' % len(errors) + '\n'.join(errors)
