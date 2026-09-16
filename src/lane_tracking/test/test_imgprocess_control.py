"""Tam kamera genisligine yayilan serit kontrol olcegi testleri."""

import numpy as np
import pytest
from sensor_msgs.msg import Image

from lane_tracking.imgprocess_node import (
    ImgProcessNode,
    apply_inner_wheel_stop,
    apply_deadband,
    clamp_inner_wheel_reversal,
    combine_lane_errors,
    compute_lane_turn_command,
    compute_pd_angular,
    enforce_minimum_wheel_speed,
    image_message_to_bgr,
    lane_end_alignment_valid,
    lane_end_confirmed,
    lane_motion_speed,
    lane_tracking_demand,
    schedule_lane_linear_speed,
    scale_lane_error,
    shape_lane_control_error,
    wheel_targets_to_twist,
)


def test_arka_kamera_modu_serit_hizini_negatif_yapar():
    assert lane_motion_speed(0.125, reverse_motion=True) == -0.125
    assert lane_motion_speed(0.125, reverse_motion=False) == 0.125
    assert lane_motion_speed(-0.125, reverse_motion=False) == 0.125


def test_ros_bgr8_mesaji_opencv_karesine_cevrilir():
    msg = Image()
    msg.width = 2
    msg.height = 1
    msg.encoding = 'bgr8'
    msg.step = 6
    msg.data = bytes([1, 2, 3, 4, 5, 6])

    frame = image_message_to_bgr(msg)

    assert frame.shape == (1, 2, 3)
    assert np.array_equal(frame[0, 1], [4, 5, 6])


def test_serit_sonu_yalniz_hizali_aracta_kurulur():
    assert lane_end_alignment_valid(0.10, 0.08, 0.20, 0.18)
    assert not lane_end_alignment_valid(0.30, 0.08, 0.20, 0.18)
    assert not lane_end_alignment_valid(0.10, 0.25, 0.20, 0.18)


def test_pd_ros_dt_ile_p_ve_d_terimi_uretir():
    angular, error, derivative = compute_pd_angular(
        error_px=-80.0,
        half_frame_width=160.0,
        previous_error=-0.25,
        dt=0.05,
        kp=0.08,
        kd=0.01,
        max_angular_speed=0.10,
        previous_derivative=0.0,
        derivative_alpha=1.0,
    )

    assert error == pytest.approx(-0.5)
    assert derivative == pytest.approx(-5.0)
    assert angular == pytest.approx(-0.09)


def test_pd_ilk_karede_turev_uretmez_ve_cikisi_sinirlar():
    angular, error, derivative = compute_pd_angular(
        error_px=160.0,
        half_frame_width=160.0,
        previous_error=None,
        dt=None,
        kp=0.50,
        kd=0.50,
        max_angular_speed=0.10,
    )

    assert error == 1.0
    assert derivative == 0.0
    assert angular == 0.10


def test_pd_alt_ofseti_ve_serit_egimini_zit_isaretle_birlestirir():
    angular, error, derivative = compute_pd_angular(
        error_px=64.0,
        half_frame_width=320.0,
        previous_error=None,
        dt=None,
        kp=0.08,
        kd=0.001,
        max_angular_speed=0.10,
        position_gain=1.20,
        heading_error=0.20,
        heading_gain=0.35,
        center_deadband_ratio=0.0,
    )

    assert error == pytest.approx(1.20 * 0.20 - 0.35 * 0.20)
    assert derivative == 0.0
    assert angular == pytest.approx(0.08 * error)


def test_pd_merkez_olu_bolgesinde_donus_uretmez():
    angular, error, _ = compute_pd_angular(
        error_px=3.0,
        half_frame_width=320.0,
        previous_error=None,
        dt=None,
        kp=0.08,
        kd=0.001,
        max_angular_speed=0.10,
        center_deadband_ratio=0.03,
    )

    assert error == 0.0
    assert angular == 0.0


@pytest.mark.parametrize(
    ('error', 'normalized', 'scaled', 'angular'),
    [
        (0.0, 0.0, 0.0, 0.0),
        (160.0, 0.5, 0.5, -0.025),
        (-160.0, -0.5, -0.5, 0.025),
        (320.0, 1.0, 1.0, -0.050),
        (-320.0, -1.0, -1.0, 0.050),
        (500.0, 1.0, 1.0, -0.050),
    ],
)
def test_hata_tam_kamera_genisligine_olceklenir(
        error, normalized, scaled, angular):
    actual_normalized, actual_scaled, actual_angular = scale_lane_error(
        error, half_frame_width=320, max_angular_speed=0.050,
        center_deadband_ratio=0.0)

    assert actual_normalized == pytest.approx(normalized)
    assert actual_scaled == pytest.approx(scaled)
    assert actual_angular == pytest.approx(angular)


def test_gecersiz_kamera_genisligi_guvenli_sifir_doner():
    assert scale_lane_error(100.0, 0, 0.050) == (0.0, 0.0, 0.0)


def test_merkez_olu_bolgesinde_donus_uretilmez():
    normalized, scaled, angular = scale_lane_error(
        3.0, half_frame_width=320, max_angular_speed=0.050,
        center_deadband_ratio=0.01)

    assert normalized == pytest.approx(0.009375)
    assert scaled == 0.0
    assert angular == 0.0


def test_olu_band_disinda_tepki_lineer_artiyor():
    normalized, scaled, angular = scale_lane_error(
        32.0, half_frame_width=320, max_angular_speed=0.050,
        center_deadband_ratio=0.01)

    assert normalized == pytest.approx(0.1)
    assert scaled == pytest.approx((0.1 - 0.01) / 0.99)
    assert angular == pytest.approx(-0.0045454545)


def test_deadband_merkezde_sifir_kenarda_lineer_artar():
    assert apply_deadband(0.009, 0.01) == 0.0
    assert apply_deadband(0.10, 0.01) == pytest.approx((0.10 - 0.01) / 0.99)
    assert apply_deadband(-0.10, 0.01) == pytest.approx(-(0.10 - 0.01) / 0.99)


def test_merkez_kazanci_dis_bolgede_tam_otoriteyi_korur():
    assert shape_lane_control_error(0.30, 0.60, 0.55) == pytest.approx(0.165)
    assert shape_lane_control_error(-0.60, 0.60, 0.55) == pytest.approx(-0.33)
    assert shape_lane_control_error(1.0, 0.60, 0.55) == pytest.approx(1.0)


def test_donuste_yavas_teker_kalkis_esiginin_altina_dusmez():
    angular = 0.040
    separation = 0.460
    linear = enforce_minimum_wheel_speed(
        linear_speed=0.024,
        angular_speed=angular,
        wheel_separation=separation,
        minimum_wheel_speed=0.055,
    )
    half_track = separation * 0.5

    assert linear == pytest.approx(0.0642)
    assert linear - angular * half_track == pytest.approx(0.055)
    assert linear + angular * half_track == pytest.approx(0.0734)


def test_duzlukte_mevcut_hiz_degismez():
    linear = enforce_minimum_wheel_speed(
        linear_speed=0.060,
        angular_speed=0.0,
        wheel_separation=0.460,
        minimum_wheel_speed=0.055,
    )

    assert linear == pytest.approx(0.060)


def _speed_for_rpm(rpm, radius=0.125):
    return float(rpm) * 2.0 * np.pi * float(radius) / 60.0


def test_reverse_donuste_sag_ic_teker_durur():
    left, right, stopped = apply_inner_wheel_stop(
        -0.080, -_speed_for_rpm(1.8), 0.125, 2.0, 3.0)

    assert left == pytest.approx(-0.080)
    assert right == 0.0
    assert stopped == 'right'


def test_reverse_donuste_sol_ic_teker_durur():
    left, right, stopped = apply_inner_wheel_stop(
        -_speed_for_rpm(1.8), -0.080, 0.125, 2.0, 3.0)

    assert left == 0.0
    assert right == pytest.approx(-0.080)
    assert stopped == 'left'


def test_reverse_sag_ic_teker_tersine_gecemez():
    left, right = clamp_inner_wheel_reversal(-0.080, 0.010, -0.035)

    assert left == pytest.approx(-0.080)
    assert right == 0.0


def test_reverse_ayni_yondeki_ic_teker_degismez():
    left, right = clamp_inner_wheel_reversal(-0.080, -0.030, -0.055)

    assert left == pytest.approx(-0.080)
    assert right == pytest.approx(-0.030)


def test_forward_sag_ic_teker_tersine_gecemez():
    left, right = clamp_inner_wheel_reversal(0.080, -0.010, 0.035)

    assert left == pytest.approx(0.080)
    assert right == 0.0


def test_normal_duz_teker_hedefleri_degismez():
    left, right = clamp_inner_wheel_reversal(0.060, 0.060, 0.060)

    assert left == pytest.approx(0.060)
    assert right == pytest.approx(0.060)


def test_ic_teker_stop_histerezisi_3_rpm_ustunde_birakir():
    stopped = None
    for rpm in (1.8, 2.5):
        left, right, stopped = apply_inner_wheel_stop(
            -0.080, -_speed_for_rpm(rpm), 0.125, 2.0, 3.0,
            stopped)
        assert left == pytest.approx(-0.080)
        assert right == 0.0
        assert stopped == 'right'

    left, right, stopped = apply_inner_wheel_stop(
        -0.080, -_speed_for_rpm(3.1), 0.125, 2.0, 3.0, stopped)
    assert left == pytest.approx(-0.080)
    assert right == pytest.approx(-_speed_for_rpm(3.1))
    assert stopped is None


def test_duz_dusuk_hizda_tekerler_degismez():
    speed = -_speed_for_rpm(1.8)
    left, right, stopped = apply_inner_wheel_stop(
        speed, speed, 0.125, 2.0, 3.0, 'right')

    assert left == pytest.approx(speed)
    assert right == pytest.approx(speed)
    assert stopped is None


def test_final_teker_hedeflerinden_twist_yeniden_olusturulur():
    linear, angular = wheel_targets_to_twist(0.0, -0.080, 0.460)

    assert linear == pytest.approx(-0.040)
    assert angular == pytest.approx(-0.080 / 0.460)


class _CommandPublisher:

    def __init__(self):
        self.messages = []

    def publish(self, message):
        self.messages.append(message)


def test_pd_last_command_gercek_yayinlanan_twisti_tutar():
    node = ImgProcessNode.__new__(ImgProcessNode)
    node.wheel_separation = 0.460
    node.wheel_radius = 0.125
    node.lane_inner_wheel_stop_rpm = 2.0
    node.lane_inner_wheel_resume_rpm = 3.0
    node._lane_inner_wheel_stopped = None
    node.max_angular_speed = 0.250
    node.pub_cmd_vel = _CommandPublisher()
    inner_speed = -_speed_for_rpm(1.8)
    raw_linear, raw_angular = wheel_targets_to_twist(
        -0.080, inner_speed, node.wheel_separation)

    left, right, final_linear, final_angular = (
        node._publish_pd_wheel_command(raw_linear, raw_angular))
    published = node.pub_cmd_vel.messages[-1]

    assert left == pytest.approx(-0.080)
    assert right == 0.0
    assert published.linear.x == pytest.approx(final_linear)
    assert published.angular.z == pytest.approx(final_angular)
    assert node.last_lane_command == pytest.approx(
        (published.linear.x, published.angular.z))


def test_pd_reversal_korumasi_final_twiste_uygulanir():
    node = ImgProcessNode.__new__(ImgProcessNode)
    node.wheel_separation = 0.460
    node.wheel_radius = 0.125
    node.lane_inner_wheel_stop_rpm = 2.0
    node.lane_inner_wheel_resume_rpm = 3.0
    node._lane_inner_wheel_stopped = None
    node.max_angular_speed = 0.250
    node.pub_cmd_vel = _CommandPublisher()
    raw_linear, raw_angular = wheel_targets_to_twist(
        -0.080, 0.010, node.wheel_separation)

    left, right, final_linear, final_angular = (
        node._publish_pd_wheel_command(raw_linear, raw_angular))

    assert left == pytest.approx(-0.080)
    assert right == 0.0
    assert final_linear == pytest.approx(-0.040)
    assert final_angular == pytest.approx(0.080 / 0.460)
    assert node._lane_inner_wheel_stopped == 'right'


def test_lane_control_reset_inner_wheel_histerezisini_temizler():
    node = ImgProcessNode.__new__(ImgProcessNode)
    node.filtered_lane_angular = 0.1
    node._pd_previous_error = 0.2
    node._pd_previous_time = object()
    node._pd_derivative = 0.3
    node.lane_missed_frames = 2
    node.last_lane_command = (-0.05, 0.1)
    node._lane_inner_wheel_stopped = 'right'
    node.lane_seen_frames = 10
    node.lane_end_reported = True
    node.lane_end_armed = True

    node._reset_lane_control()

    assert node._lane_inner_wheel_stopped is None


def test_pd_donusu_buyudukce_ileri_hiz_azalir():
    assert schedule_lane_linear_speed(
        0.052360, 0.020944, 0.0, 0.045530) == pytest.approx(0.052360)
    assert schedule_lane_linear_speed(
        0.052360, 0.020944, 0.022765, 0.045530) == pytest.approx(0.036652)
    assert schedule_lane_linear_speed(
        0.052360, 0.020944, 0.045530, 0.045530) == pytest.approx(0.020944)


def test_hiz_plani_birbirini_iptal_eden_serit_hatalarini_korur():
    demand = lane_tracking_demand(
        position_error=0.14,
        heading_error=0.15,
        position_gain=2.0,
        heading_gain=4.0,
        control_error=-0.32,
    )

    assert demand == pytest.approx(0.60)


def test_merkez_ve_yon_hatasi_lineer_birlesir():
    combined, angular = combine_lane_errors(
        position_error=0.20,
        heading_error=0.40,
        heading_gain=0.35,
        max_angular_speed=0.075,
    )

    assert combined == pytest.approx(0.34)
    assert angular == pytest.approx(-0.0255)


def test_birlesik_hata_kamera_kenarinda_sinirlanir():
    combined, angular = combine_lane_errors(
        position_error=0.90,
        heading_error=0.80,
        heading_gain=0.35,
        max_angular_speed=0.075,
    )

    assert combined == 1.0
    assert angular == pytest.approx(-0.075)


def test_offset_heading_modu_yanal_ofset_ve_yonu_birlestirir():
    mode, offset_term, combined, angular = compute_lane_turn_command(
        control_mode='offset_heading',
        normalized_error=0.20,
        scaled_error=0.19,
        heading_error=0.30,
        offset_gain=0.85,
        heading_gain=0.55,
        center_deadband_ratio=0.01,
        max_angular_speed=0.12,
    )

    assert mode == 'offset_heading'
    assert offset_term == pytest.approx((0.20 - 0.01) / 0.99)
    assert combined == pytest.approx(0.85 * offset_term + 0.55 * 0.30)
    assert angular == pytest.approx(-combined * 0.12)


def test_legacy_modu_onceki_birlesimi_korur():
    mode, position_term, combined, angular = compute_lane_turn_command(
        control_mode='legacy',
        normalized_error=0.20,
        scaled_error=0.25,
        heading_error=0.40,
        offset_gain=0.85,
        heading_gain=0.35,
        center_deadband_ratio=0.01,
        max_angular_speed=0.075,
    )

    assert mode == 'legacy'
    assert position_term == pytest.approx(0.25)
    assert combined == pytest.approx(0.39)
    assert angular == pytest.approx(-0.02925)


def test_kamera_acilisindaki_serit_yoklugu_son_sayilmaz():
    assert not lane_end_confirmed(
        seen_frames=0, missed_frames=30, minimum_seen_frames=15,
        missing_frames=6, loss_hold_frames=3)


def test_gecici_serit_kaybi_son_sayilmaz():
    assert not lane_end_confirmed(
        seen_frames=60, missed_frames=3, minimum_seen_frames=15,
        missing_frames=6, loss_hold_frames=3)


def test_yeterince_izlenen_seridin_kalici_kaybi_son_sayilir():
    assert lane_end_confirmed(
        seen_frames=60, missed_frames=9, minimum_seen_frames=15,
        missing_frames=9, loss_hold_frames=3)


def test_yalniz_serit_modunda_serit_sonu_devre_disidir():
    assert not lane_end_confirmed(
        seen_frames=200, missed_frames=200, minimum_seen_frames=15,
        missing_frames=9, loss_hold_frames=3, enabled=False)
