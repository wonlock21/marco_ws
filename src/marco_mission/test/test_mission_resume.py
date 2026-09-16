"""Mission checkpoint and safe resume regression tests."""

import threading

import pytest

from marco_mission.localization_validity import LocalizationHealth
from marco_mission.mission_manager import MissionAbort, MissionManager
from marco_msgs.msg import RobotStatus
from marco_msgs.srv import ResumeMission


def _run_manager(
    *,
    start_index=0,
    loaded=False,
    return_home=False,
    failure=None,
    fallback_station='',
):
    manager = MissionManager.__new__(MissionManager)
    manager._route_nodes = ['A1', 'B2']
    manager._current_stop_index = start_index
    manager._station_exit_pending = ''
    manager._station_exit_pending_loaded = False
    manager._loaded = loaded
    manager._return_home = return_home
    manager._home_node = 'HOME'
    manager._current_node = 'HOME'
    manager._nodes = {
        'A1': {'role': 'pickup_dock'},
        'B2': {'role': 'dropoff_dock'},
    }
    manager._pickup = 'A1'
    manager._dropoff = 'B2'
    manager._task_id = 'task-42'
    manager._source = 'gui'
    manager._mission_field_hash = 'field-hash'
    manager._mission_graph_file = '/fields/route.geojson'
    manager._resume_context_valid = False
    manager._mission_started_wall = 0.0
    manager._mission_elapsed = 0.0
    manager._gate_ok = False
    manager._gate_entry_node = ''
    manager._gate_direction = ''
    manager._gate_crossing_id = ''
    manager._state = RobotStatus.STATE_TASK_RECEIVED
    manager._estop = False
    manager._latched_abort = False
    manager._busy = True
    manager._running = True
    manager._active_goal = None
    manager._active_kind = ''
    manager._station_phase = manager._STATION_IDLE
    manager._lock = threading.RLock()
    manager.operations = []
    manager.events = []
    failure_state = {
        'step': failure[0] if failure else '',
        'station': failure[1] if failure else '',
        'used': False,
    }

    def operation(step, station='', *details):
        manager.operations.append((step, station, *details))
        if (
            not failure_state['used']
            and failure_state['step'] == step
            and failure_state['station'] == station
        ):
            failure_state['used'] = True
            raise MissionAbort(f'{step}:{station} failed')

    manager._set_state = lambda state, next_node='': manager.operations.append(
        ('state', next_node, state)
    )
    manager._begin_station_approach = lambda station: operation(
        'begin', station)
    manager._station_approach_target = lambda station: f'{station}_approach'

    def navigate(target, loaded):
        operation('navigate', target, loaded)
        manager._current_node = target

    def navigate_via_gate(target, loaded, direction):
        operation('gate', target, loaded, direction)
        manager._current_node = target

    manager._navigate = navigate
    manager._navigate_via_gate = navigate_via_gate
    manager._wait_until_stopped = lambda label: operation('stopped', label)
    manager._turn_at_station = lambda station: operation('turn', station)

    def dock(station, pickup):
        mode = 'fallback' if station == fallback_station else 'lane'
        operation('dock', station, pickup, mode)

    manager._do_dock = dock
    manager._do_lift = lambda station, pickup: operation(
        'lift', station, pickup)

    def publish_load_state(value):
        manager._loaded = bool(value)
        manager.operations.append(('load', '', bool(value)))

    manager._publish_load_state = publish_load_state
    manager._exit_station = lambda station, loaded: operation(
        'exit', station, loaded)
    manager._safe_stop = lambda: manager.operations.append(('stop', ''))
    manager._notify_complete = lambda success, reason: manager.operations.append(
        ('complete', '', success, reason)
    )
    manager._event = lambda name, **fields: manager.events.append(
        (name, fields)
    )
    manager.failure_state = failure_state
    return manager


def _retry(manager):
    manager.failure_state['step'] = ''
    manager._busy = True
    manager._running = True
    before = len(manager.operations)
    manager._run()
    return manager.operations[before:]


@pytest.mark.parametrize('failure_step', ['navigate', 'dock'])
def test_pickup_pre_lift_failure_retries_same_station(failure_step):
    target = 'A1_approach' if failure_step == 'navigate' else 'A1'
    manager = _run_manager(failure=(failure_step, target))

    manager._run()

    assert manager._current_stop_index == 0
    assert manager._loaded is False
    assert manager._resume_context_valid is True
    assert not any(item[0] == 'complete' for item in manager.operations)

    retry_operations = _retry(manager)

    assert ('begin', 'A1') in retry_operations
    assert ('lift', 'A1', True) in retry_operations


def test_pickup_success_commits_dropoff_before_exit_failure():
    manager = _run_manager(failure=('exit', 'A1'))

    manager._run()

    assert manager._current_stop_index == 1
    assert manager._loaded is True

    retry_operations = _retry(manager)

    assert ('begin', 'A1') not in retry_operations
    assert ('lift', 'A1', True) not in retry_operations
    exit_index = retry_operations.index(('exit', 'A1', True))
    begin_dropoff_index = retry_operations.index(('begin', 'B2'))
    assert exit_index < begin_dropoff_index
    assert ('begin', 'B2') in retry_operations
    assert ('dock', 'B2', False, 'lane') in retry_operations


def test_dropoff_failure_retries_dropoff_with_load_preserved():
    manager = _run_manager(
        start_index=1,
        loaded=True,
        failure=('dock', 'B2'),
    )

    manager._run()

    assert manager._current_stop_index == 1
    assert manager._loaded is True

    retry_operations = _retry(manager)

    assert ('begin', 'B2') in retry_operations
    assert ('lift', 'B2', False) in retry_operations


def test_dropoff_success_checkpoint_skips_repeat_and_returns_home():
    manager = _run_manager(
        start_index=1,
        loaded=True,
        return_home=True,
        failure=('exit', 'B2'),
    )

    manager._run()

    assert manager._current_stop_index == 2
    assert manager._loaded is False

    retry_operations = _retry(manager)

    assert not any(
        item[0] in ('begin', 'dock', 'lift')
        for item in retry_operations
    )
    exit_index = retry_operations.index(('exit', 'B2', False))
    return_index = retry_operations.index(('gate', 'HOME', False, 'return'))
    assert exit_index < return_index


def test_lane_nav2_fallback_success_still_commits_only_after_lift():
    manager = _run_manager(
        failure=('exit', 'A1'),
        fallback_station='A1',
    )

    manager._run()

    dock_index = manager.operations.index(('dock', 'A1', True, 'fallback'))
    lift_index = manager.operations.index(('lift', 'A1', True))
    load_index = manager.operations.index(('load', '', True))
    assert dock_index < lift_index < load_index
    assert manager._current_stop_index == 1


def _resume_manager():
    manager = MissionManager.__new__(MissionManager)
    manager._lock = threading.RLock()
    manager._busy = False
    manager._running = False
    manager._resume_context_valid = True
    manager._active_goal = None
    manager._active_kind = ''
    manager._estop = False
    manager._latched_abort = False
    manager._obstacle = False
    manager._route_nodes = ['A1', 'B2']
    manager._current_stop_index = 1
    manager._loaded = True
    manager._return_home = True
    manager._home_node = 'HOME'
    manager._task_id = 'task-42'
    manager._source = 'gui'
    manager._pickup = 'A1'
    manager._dropoff = 'B2'
    manager._state = RobotStatus.STATE_ERROR
    manager._abort_reason = 'transient failure'
    manager._status_detail = 'transient failure'
    manager._next_node = ''
    manager._require_active_field = True
    manager._active_field_ready = True
    manager._active_field_hash = 'field-hash'
    manager._mission_field_hash = 'field-hash'
    manager._graph_file = '/fields/route.geojson'
    manager._mission_graph_file = '/fields/route.geojson'
    manager._production_route_ready = lambda: True
    manager._validate_route = lambda _route: None
    manager._base_ok = True
    manager._base_communication_healthy = lambda: manager._base_ok
    manager._safety_supervisor_healthy = lambda: True
    manager._lift_server_healthy = lambda: True
    manager._localization = LocalizationHealth(True, 'hazir')
    manager._localization_health = lambda: manager._localization
    manager._plc_connection_healthy = lambda: True
    manager.events = []
    manager._event = lambda name, **fields: manager.events.append(
        (name, fields)
    )
    manager.starts = 0

    def start():
        manager.starts += 1

    manager._start_mission_thread = start
    return manager


def _resume(manager):
    return manager._on_resume(
        ResumeMission.Request(), ResumeMission.Response())


@pytest.mark.parametrize(
    'configure,expected',
    [
        (lambda manager: setattr(manager, '_estop', True), 'e-stop'),
        (
            lambda manager: setattr(
                manager,
                '_localization',
                LocalizationHealth(False, 'TF stale'),
            ),
            'lokalizasyon gecersiz',
        ),
        (lambda manager: setattr(manager, '_base_ok', False), 'STM32/UART'),
        (lambda manager: setattr(manager, '_busy', True), 'aktif gorev'),
        (
            lambda manager: setattr(manager, '_active_goal', object()),
            'action halen aktif',
        ),
        (
            lambda manager: setattr(
                manager, '_active_field_hash', 'another-field'),
            'checkpoint sahasiyla ayni degil',
        ),
        (
            lambda manager: setattr(
                manager, '_resume_context_valid', False),
            'devam ettirilebilir gorev yok',
        ),
    ],
)
def test_resume_rejects_unsafe_or_unavailable_state(configure, expected):
    manager = _resume_manager()
    configure(manager)

    response = _resume(manager)

    assert response.accepted is False
    assert expected in response.message
    assert manager.starts == 0


def test_resume_accepts_checkpoint_and_preserves_context():
    manager = _resume_manager()

    response = _resume(manager)

    assert response.accepted is True
    assert manager.starts == 1
    assert manager._task_id == 'task-42'
    assert manager._route_nodes == ['A1', 'B2']
    assert manager._current_stop_index == 1
    assert manager._loaded is True
    assert manager._return_home is True
    resumed = next(
        fields for name, fields in manager.events
        if name == 'mission_resumed'
    )
    assert resumed == {
        'task_id': 'task-42',
        'current_stop_index': 1,
        'station': 'B2',
        'loaded': True,
    }


def test_new_mission_reservation_invalidates_old_resume_context():
    manager = _resume_manager()
    manager._known_task_ids = {'task-42'}
    manager._plc_assign_inflight = False

    error = manager._reserve(
        'task-43',
        ['A1', 'B2'],
        'gui',
        start_immediately=False,
    )

    assert error is None
    assert manager._resume_context_valid is False
    assert manager._task_id == 'task-43'


def test_completed_mission_clears_resume_context():
    manager = _run_manager()

    manager._run()

    assert manager._resume_context_valid is False
    assert manager._current_stop_index == len(manager._route_nodes)
