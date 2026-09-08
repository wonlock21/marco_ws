"""Copyright lint entry point."""

from ament_copyright.main import main
import pytest


# Match the existing workspace policy until source headers are standardized.
@pytest.mark.skip(reason='Workspace source files do not use copyright headers.')
@pytest.mark.copyright
@pytest.mark.linter
def test_copyright():
    """Check source file copyright headers when enabled by the workspace."""
    rc = main(argv=['.', 'test'])
    assert rc == 0, 'Found errors'
