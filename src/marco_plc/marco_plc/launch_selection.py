"""Resolve exactly one PLC service provider for launch files."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlcBackendSelection:
    """Resolved provider and matching Mission Manager source label."""

    backend: str
    task_source: str

    @property
    def start_mock(self) -> bool:
        """Return whether the simulation provider must be started."""
        return self.backend == 'mock'

    @property
    def start_real(self) -> bool:
        """Return whether the production bridge must be started."""
        return self.backend == 'real'


def select_plc_backend(backend: str, task_source: str) -> PlcBackendSelection:
    """Resolve explicit selection or preserve the legacy task-source default."""
    backend = str(backend).strip().lower()
    task_source = str(task_source).strip().lower()
    if backend == 'auto':
        mapping = {'mock_plc': 'mock', 'plc': 'real'}
        try:
            backend = mapping[task_source]
        except KeyError as error:
            raise ValueError(
                f'auto PLC backend icin gecersiz task_source: {task_source!r}'
            ) from error
    if backend not in ('mock', 'real'):
        raise ValueError(f'plc_backend mock veya real olmali: {backend!r}')
    return PlcBackendSelection(
        backend=backend,
        task_source='mock_plc' if backend == 'mock' else 'plc',
    )
