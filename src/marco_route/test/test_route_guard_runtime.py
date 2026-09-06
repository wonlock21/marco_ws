from types import SimpleNamespace

from std_msgs.msg import Bool

from marco_route.route_guard_core import RouteEdge
from marco_route.route_guard_node import RouteGuard


class _Publisher:
    def __init__(self):
        self.values = []

    def publish(self, message):
        self.values.append(bool(message.data))


class _Future:
    def __init__(self, response):
        self._response = response

    def done(self):
        return True

    def result(self):
        return self._response


class _DynamicClient:
    def __init__(self):
        self.requests = []

    def service_is_ready(self):
        return True

    def call_async(self, request):
        self.requests.append(request)
        return _Future(SimpleNamespace(success=True))


def _guard():
    guard = RouteGuard.__new__(RouteGuard)
    guard._graph = SimpleNamespace(edges=(RouteEdge(
        feature_id=7,
        logical_id=70,
        start_feature_id=1,
        end_feature_id=2,
        start_name="A",
        end_name="B",
        points=((0.0, 0.0), (1.0, 0.0)),
        max_speed=0.2,
        load_rule="loaded",
        movement_direction="forward",
        gate_event="",
    ),))
    guard._loaded = False
    guard._desired_closed = {7}
    guard._applied_closed = set()
    guard._constraints_applied_once = False
    guard._constraint_generation = 0
    guard._dynamic_generation = -1
    guard._dynamic_future = None
    guard._constraints_ready = False
    guard._constraints_pub = _Publisher()
    guard._dynamic = _DynamicClient()
    guard._event = lambda *args, **kwargs: None
    return guard


def test_constraints_ready_requires_successful_dynamic_edges_response():
    guard = _guard()

    guard._update_dynamic_edges()

    assert len(guard._dynamic.requests) == 1
    assert guard._constraints_ready is False
    assert guard._constraints_pub.values == []

    guard._update_dynamic_edges()

    assert guard._constraints_applied_once is True
    assert guard._constraints_ready is True
    assert guard._constraints_pub.values == [True]


def test_load_transition_forces_another_dynamic_edges_round_trip():
    guard = _guard()
    guard._update_dynamic_edges()
    guard._update_dynamic_edges()
    assert guard._constraints_ready is True

    guard._on_load(Bool(data=True))

    assert guard._constraints_applied_once is False
    assert guard._constraints_ready is False
    assert guard._constraints_pub.values[-1] is False
    guard._update_dynamic_edges()
    assert len(guard._dynamic.requests) == 2
    assert guard._constraints_ready is False
    guard._update_dynamic_edges()
    assert guard._constraints_ready is True


def test_stale_dynamic_response_cannot_mark_new_load_state_ready():
    guard = _guard()
    guard._update_dynamic_edges()
    assert guard._dynamic_future is not None

    guard._on_load(Bool(data=True))
    guard._update_dynamic_edges()

    assert guard._constraints_ready is False
    assert guard._constraints_applied_once is False
    assert len(guard._dynamic.requests) == 2
    guard._update_dynamic_edges()
    assert guard._constraints_ready is True


def test_hard_stop_requires_continuous_deviation_for_debounce_period():
    guard = RouteGuard.__new__(RouteGuard)
    guard._stop_debounce = 0.5
    guard._stop_candidate_wall = None

    assert guard._confirmed_stop(True, 10.0) is False
    assert guard._confirmed_stop(True, 10.49) is False
    assert guard._confirmed_stop(True, 10.50) is True


def test_stop_debounce_resets_when_deviation_recovers():
    guard = RouteGuard.__new__(RouteGuard)
    guard._stop_debounce = 0.5
    guard._stop_candidate_wall = None

    assert guard._confirmed_stop(True, 10.0) is False
    assert guard._confirmed_stop(False, 10.3) is False
    assert guard._confirmed_stop(True, 10.6) is False
    assert guard._confirmed_stop(True, 11.1) is True
