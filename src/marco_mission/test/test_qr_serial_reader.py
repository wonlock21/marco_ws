"""QR serial reader payload validation tests."""

from marco_mission.qr_serial_reader import (
    COMPETITION_QR_VALUES,
    normalize_qr_payload,
)


def test_normalize_qr_payload_strips_scanner_line_endings():
    assert normalize_qr_payload(b'  alim2\r\n') == 'ALIM2'


def test_competition_payloads_are_exact():
    expected = {
        'BASLA',
        'ALIM1', 'ALIM2', 'ALIM3',
        'KAPI1', 'KAPI2',
        'BIRAK1', 'BIRAK2', 'BIRAK3',
    }
    assert COMPETITION_QR_VALUES == expected
    assert normalize_qr_payload('ALlM1') not in COMPETITION_QR_VALUES
