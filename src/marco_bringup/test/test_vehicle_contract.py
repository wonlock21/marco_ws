"""Kanonik arac sozlesmesini tum uretim tuketicilerine karsi denetler."""

import importlib.util
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PACKAGE_ROOT.parents[1]
CHECK_SCRIPT = PACKAGE_ROOT / 'scripts/check_vehicle_contract.py'


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        'check_vehicle_contract', CHECK_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_vehicle_contract():
    """Teker, TF, footprint ve stop bolgeleri tek sozlesmeyle uyussun."""
    _load_checker().check(WORKSPACE_ROOT)
