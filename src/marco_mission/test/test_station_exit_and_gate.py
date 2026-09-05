"""F8B station-exit and direction-specific gate handoff tests."""

from types import SimpleNamespace

import pytest

from marco_mission.mission_manager import MissionAbort, MissionManager
from marco_mission.station_qr_gate import StationQrGate


class _Publisher:
    def __init__(self, order):
        self.order = order

    def publish(self, message):
        self.order.append(("lane", message.data))


def test_station_exit_stops_lane_then_navigates_to_own_approach():
    manager = MissionManager.__new__(MissionManager)
    manager._nodes = {
        "A1": {
            "id": 1,
            "name": "A1_dock",
            "role": "pickup_dock",
            "station_id": "A1",
            "approach_qr_id": "q2",
        },
        "q2": {
            "id": 2,
            "name": "q2",
            "role": "pickup_approach",
            "station_id": "A1",
            "approach_qr_id": "",
        },
    }
    manager._qr_gate = StationQrGate()
    manager._qr_gate.arm("A1", "q2")
    assert manager._qr_gate.observe("q2", True).accepted
    manager._qr_gate.turning()
    manager._qr_gate.line_follow_ready()
    manager._qr_gate.docking()
    manager._qr_gate.docking_complete(pickup=True)
    manager._docking_lane_active = True
    order = []
    manager._task_pub = _Publisher(order)
    manager._event = lambda name, **fields: order.append(("event", name, fields))
    manager._wait_until_stopped = lambda label: order.append(("stopped", label))
    manager._navigate = lambda target, loaded: order.append(
        ("nav", target, loaded)
    )

    MissionManager._exit_station(manager, "A1", loaded=True)

    lane_index = order.index(("lane", "STOP"))
    stopped_index = next(
        index for index, item in enumerate(order) if item[0] == "stopped"
    )
    nav_index = order.index(("nav", "q2", True))
    assert lane_index < stopped_index < nav_index
    assert manager._qr_gate.phase == StationQrGate.EXITING
    assert not manager._qr_gate.armed
    assert manager._docking_lane_active is False
    assert [item for item in order if item[0] == "lane"] == [
        ("lane", "STOP")
    ]


def _gate_manager(reply_crossing_id=None):
    manager = MissionManager.__new__(MissionManager)
    manager._gate_node = "q5"
    manager._return_gate_node = "q6"
    manager._gate_sequence = 0
    manager._gate_ok = False
    manager._gate_entry_node = ""
    manager._gate_direction = ""
    manager._gate_crossing_id = ""
    manager._task_id = "task-42"
    manager._gate = object()
    manager._gate_timeout = 1.0
    manager.calls = []
    manager.requests = []
    manager._navigate = lambda target, loaded: manager.calls.append(
        ("nav", target, loaded)
    )
    manager._wait_until_stopped = lambda label: manager.calls.append(
        ("stopped", label)
    )
    manager._set_state = lambda state, node="": manager.calls.append(
        ("state", state, node)
    )
    manager._event = lambda name, **fields: manager.calls.append(
        ("event", name, fields)
    )

    def service_call(_client, request, _timeout, _label):
        manager.requests.append(request)
        response_id = (
            request.crossing_id
            if reply_crossing_id is None else reply_crossing_id
        )
        return SimpleNamespace(
            granted=True,
            crossing_id=response_id,
            message="ok",
        )

    manager._service_call = service_call
    return manager


def test_each_direction_uses_its_own_entry_and_fresh_permission():
    manager = _gate_manager()

    MissionManager._navigate_via_gate(
        manager, "B2_approach", loaded=True, direction="outbound"
    )
    MissionManager._navigate_via_gate(
        manager, "WAIT", loaded=False, direction="return"
    )

    assert [(item.node_id, item.direction) for item in manager.requests] == [
        ("q5", "outbound"),
        ("q6", "return"),
    ]
    assert all(item.task_id == "task-42" for item in manager.requests)
    assert manager.requests[0].crossing_id != manager.requests[1].crossing_id
    assert [item for item in manager.calls if item[0] == "nav"] == [
        ("nav", "q5", True),
        ("nav", "B2_approach", True),
        ("nav", "q6", False),
        ("nav", "WAIT", False),
    ]
    assert manager._gate_ok is False
    assert manager._gate_direction == ""


def test_stale_gate_reply_cannot_authorize_crossing():
    manager = _gate_manager(reply_crossing_id="old-crossing")

    with pytest.raises(MissionAbort, match="eski/gecersiz"):
        MissionManager._navigate_via_gate(
            manager, "B2_approach", loaded=True, direction="outbound"
        )

    assert [item for item in manager.calls if item[0] == "nav"] == [
        ("nav", "q5", True),
    ]
    assert manager._gate_ok is False
    assert manager._gate_crossing_id == ""
