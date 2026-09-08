"""Byte-level tests for the specified SRU UDP protocol."""

import math
import struct

import pytest

from marco_msgs.msg import RobotStatus
from marco_plc.transports.base import RobotStatusSnapshot
from marco_plc.transports.sru_udp import (
    SruPacketError,
    decode_rx_packet,
    encode_tx_packet,
)


def _status(state=RobotStatus.STATE_IDLE, pickup='', dropoff='', x=0.0, y=0.0):
    return RobotStatusSnapshot(state, pickup, dropoff, x, y)


@pytest.mark.parametrize(
    ('mission_state', 'wire_state'),
    (
        (RobotStatus.STATE_IDLE, 1),
        (RobotStatus.STATE_TASK_RECEIVED, 2),
        (RobotStatus.STATE_MOVING_UNLOADED, 3),
        (RobotStatus.STATE_MOVING_LOADED, 4),
        (RobotStatus.STATE_WAITING_PLC, 5),
        (RobotStatus.STATE_RETURNING, 6),
        (RobotStatus.STATE_ERROR, 7),
        (RobotStatus.STATE_ESTOP, 8),
    ),
)
def test_robot_status_mapping_is_explicit(mission_state, wire_state):
    """Map every zero-based RobotStatus state to the required wire value."""
    packet = encode_tx_packet(_status(state=mission_state))
    assert len(packet) == 7
    assert packet[0] == wire_state


@pytest.mark.parametrize('pickup,code', (('A1', 1), ('A2', 2), ('A3', 3)))
def test_pickup_station_mapping(pickup, code):
    """Encode all supported pickup stations."""
    assert encode_tx_packet(_status(pickup=pickup))[1] == code


@pytest.mark.parametrize('dropoff,code', (('B1', 1), ('B2', 2), ('B3', 3)))
def test_dropoff_station_mapping(dropoff, code):
    """Encode all supported dropoff stations."""
    assert encode_tx_packet(_status(dropoff=dropoff))[2] == code


def test_signed_coordinates_are_little_endian_int16():
    """Encode positive and negative map coordinates as truncated centimetres."""
    packet = encode_tx_packet(_status(x=1.239, y=-1.239))
    assert packet == bytes((1, 0, 0, 123, 0, 133, 255))
    assert struct.unpack('<BBBhh', packet) == (1, 0, 0, 123, -123)


@pytest.mark.parametrize(
    'status',
    (_status(pickup='A4'), _status(dropoff='B4'), _status(state=99)),
)
def test_invalid_tx_state_or_station_is_rejected(status):
    """Reject unknown state and assignment names instead of inventing codes."""
    with pytest.raises(SruPacketError):
        encode_tx_packet(status)


@pytest.mark.parametrize('value', (math.nan, math.inf, -math.inf, 327.68, -327.69))
def test_invalid_coordinate_is_rejected_without_wrap(value):
    """Reject non-finite and overflowing coordinates."""
    with pytest.raises(SruPacketError):
        encode_tx_packet(_status(x=value))


@pytest.mark.parametrize(
    ('payload', 'pickup', 'dropoff', 'control'),
    (
        (bytes((1, 1, 1)), 'A1', 'B1', 1),
        (bytes((3, 2, 2)), 'A3', 'B2', 2),
    ),
)
def test_rx_uses_third_physical_byte_as_control(
    payload, pickup, dropoff, control
):
    """Read CONTROL from packet[2], resolving the specification typo."""
    packet = decode_rx_packet(payload)
    assert packet.pickup_node == pickup
    assert packet.dropoff_node == dropoff
    assert packet.control == control


@pytest.mark.parametrize('payload', (b'', b'\x01\x01', b'\x01\x01\x01\x00'))
def test_invalid_rx_length_is_rejected(payload):
    """Accept only the specified three-byte RX packet."""
    with pytest.raises(SruPacketError):
        decode_rx_packet(payload)


@pytest.mark.parametrize(
    'payload',
    (bytes((0, 1, 1)), bytes((1, 0, 1)), bytes((4, 1, 1)), bytes((1, 4, 1)),
     bytes((1, 1, 0)), bytes((1, 1, 3))),
)
def test_unknown_rx_station_or_control_is_rejected(payload):
    """Never interpret placeholder or unknown codes as an assignment."""
    with pytest.raises(SruPacketError):
        decode_rx_packet(payload)
