"""Tam karede adaptif maske ve geometri ile siyah serit algilama."""

import cv2
import numpy as np

from .opencl_lane import OpenClLaneMask


def adaptive_dark_mask_cpu(frame, value_max=140, block_size=81, offset=18):
    """OpenCL hatti ile ayni tamsayi hesabini CPU uzerinde uygula."""
    b = frame[:, :, 0].astype(np.int32)
    g = frame[:, :, 1].astype(np.int32)
    r = frame[:, :, 2].astype(np.int32)
    gray = ((29 * b + 150 * g + 77 * r + 128) >> 8).astype(np.uint8)

    radius = max(1, (int(block_size) - 1) // 2)
    side = radius * 2 + 1
    padded = cv2.copyMakeBorder(
        gray, radius, radius, radius, radius, cv2.BORDER_REPLICATE)
    integral = cv2.integral(padded, sdepth=cv2.CV_32S)
    local_sum = (
        integral[side:, side:]
        - integral[:-side, side:]
        - integral[side:, :-side]
        + integral[:-side, :-side]
    )
    mask = np.where(
        (gray.astype(np.int32) <= int(value_max))
        & ((gray.astype(np.int32) + int(offset)) * side * side < local_sum),
        255,
        0,
    ).astype(np.uint8)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.erode(
        mask, kernel, iterations=1,
        borderType=cv2.BORDER_CONSTANT, borderValue=255)
    return cv2.dilate(
        mask, kernel, iterations=1,
        borderType=cv2.BORDER_CONSTANT, borderValue=0)


class LaneDetector:
    def __init__(
            self, use_opencl=False, value_max=140, block_size=81,
            adaptive_offset=18, ipm_enabled=False, ipm_source_points=None,
            ipm_destination_points=None, lookahead_y=160,
            lookahead_band_half_height=5):
        self.use_opencl = use_opencl
        self.gpu_mask = OpenClLaneMask() if use_opencl else None
        self.value_max = int(value_max)
        self.block_size = int(block_size)
        self.adaptive_offset = int(adaptive_offset)
        self.ipm_enabled = bool(ipm_enabled)
        self.ipm_source_points = ipm_source_points or [
            0.20, 0.95, 0.42, 0.45, 0.58, 0.45, 0.80, 0.95]
        self.ipm_destination_points = ipm_destination_points or [
            0.20, 1.00, 0.20, 0.00, 0.80, 0.00, 0.80, 1.00]
        self.lookahead_y = int(lookahead_y)
        self.lookahead_band_half_height = max(
            1, int(lookahead_band_half_height))
        self.last_mask = None
        self.last_selected_mask = None
        self.last_debug_frame = None
        self.last_lookahead_x = None
        self.last_heading_error = 0.0
        self.last_confidence = 0.0
        self._previous_center_x = None

    def reset_tracking(self):
        """Yeni surus oturumu icin zamansal kontur hafizasini temizle."""
        self.last_heading_error = 0.0
        self.last_confidence = 0.0
        self.last_lookahead_x = None
        self._previous_center_x = None

    def process(self, frame, center_x):
        height, width = frame.shape[:2]
        working_frame = self._birdseye(frame) if self.ipm_enabled else frame
        self.last_debug_frame = working_frame
        if self.use_opencl:
            mask = self.gpu_mask.process(
                working_frame, value_max=self.value_max,
                block_size=self.block_size, offset=self.adaptive_offset)
        else:
            mask = adaptive_dark_mask_cpu(
                working_frame, value_max=self.value_max,
                block_size=self.block_size, offset=self.adaptive_offset)
        mask = self._recover_wide_lane(mask)
        self.last_mask = mask

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        selected = self._select_contour(contours, width, height)
        if selected is None:
            self.last_selected_mask = np.zeros_like(mask)
            self.last_heading_error = 0.0
            self.last_confidence = 0.0
            self.last_lookahead_x = None
            self._draw_lookahead(working_frame, center_x, None)
            return False, 0.0

        selected_mask = np.zeros_like(mask)
        cv2.drawContours(selected_mask, [selected], -1, 255, -1)
        self.last_selected_mask = selected_mask
        near_x = self._band_center(
            selected_mask, int(height * 0.72), height)
        far_x = self._band_center(
            selected_mask, int(height * 0.40), int(height * 0.68))

        moments = cv2.moments(selected)
        contour_x = (
            float(moments['m10'] / moments['m00'])
            if moments['m00'] > 0.0 else float(center_x))
        if near_x is None:
            near_x = contour_x
        if far_x is None:
            far_x = contour_x

        lookahead_y = max(0, min(height - 1, self.lookahead_y))
        lookahead_x = self._band_center(
            selected_mask,
            lookahead_y - self.lookahead_band_half_height,
            lookahead_y + self.lookahead_band_half_height + 1)
        self.last_lookahead_x = (
            float(lookahead_x) if lookahead_x is not None else None)

        half_width = max(1.0, width * 0.5)
        self.last_heading_error = max(
            -1.0, min(1.0, (far_x - near_x) / half_width))
        self._previous_center_x = near_x

        area = cv2.contourArea(selected)
        _, y, _, contour_height = cv2.boundingRect(selected)
        height_score = min(1.0, contour_height / max(1.0, height * 0.6))
        area_score = min(1.0, area / max(1.0, width * height * 0.08))
        self.last_confidence = 0.65 * height_score + 0.35 * area_score

        near_y = int(height * 0.84)
        far_y = int(height * 0.54)
        cv2.drawContours(working_frame, [selected], -1, (0, 220, 0), 2)
        cv2.circle(
            working_frame, (int(round(near_x)), near_y),
            7, (0, 255, 0), -1)
        cv2.circle(
            working_frame, (int(round(far_x)), far_y),
            6, (0, 165, 255), -1)
        cv2.line(
            working_frame, (int(round(near_x)), near_y),
            (int(round(far_x)), far_y), (0, 255, 255), 2)
        cv2.line(
            working_frame,
            (center_x, near_y), (int(round(near_x)), near_y),
            (255, 255, 0), 2)
        self._draw_lookahead(working_frame, center_x, lookahead_x)

        return True, float(near_x - center_x)

    def _recover_wide_lane(self, mask):
        """Kalin seridin adaptif esikte ayrilan iki kenarini birlestir."""
        height, width = mask.shape[:2]
        vertical_size = max(3, int(height * 0.10))
        if vertical_size % 2 == 0:
            vertical_size += 1
        vertical_kernel = np.ones((vertical_size, 1), dtype=np.uint8)
        continuous = cv2.morphologyEx(
            mask, cv2.MORPH_OPEN, vertical_kernel,
            borderType=cv2.BORDER_CONSTANT, borderValue=0)

        kernel_width = max(3, min(self.block_size, int(width * 0.25)))
        if kernel_width % 2 == 0:
            kernel_width -= 1
        kernel = np.ones((1, kernel_width), dtype=np.uint8)
        filled = cv2.morphologyEx(
            continuous, cv2.MORPH_CLOSE, kernel,
            borderType=cv2.BORDER_CONSTANT, borderValue=0)
        return cv2.morphologyEx(
            filled, cv2.MORPH_OPEN, vertical_kernel,
            borderType=cv2.BORDER_CONSTANT, borderValue=0)

    def _birdseye(self, frame):
        height, width = frame.shape[:2]
        source = self._normalized_points(
            self.ipm_source_points, width, height, 'ipm_source_points')
        destination = self._normalized_points(
            self.ipm_destination_points, width, height,
            'ipm_destination_points')
        transform = cv2.getPerspectiveTransform(source, destination)
        return cv2.warpPerspective(
            frame, transform, (width, height), flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE)

    @staticmethod
    def _normalized_points(values, width, height, name):
        if len(values) != 8:
            raise ValueError(f'{name} tam olarak 8 deger icermeli')
        points = np.asarray(values, dtype=np.float32).reshape(4, 2)
        if not np.all(np.isfinite(points)):
            raise ValueError(f'{name} sonlu sayilar icermeli')
        points[:, 0] *= max(1, width - 1)
        points[:, 1] *= max(1, height - 1)
        return points

    def _draw_lookahead(self, frame, center_x, lane_x):
        height, width = frame.shape[:2]
        y = max(0, min(height - 1, self.lookahead_y))
        cv2.line(frame, (0, y), (width - 1, y), (255, 0, 255), 1)
        cv2.circle(frame, (int(center_x), y), 5, (255, 0, 0), -1)
        if lane_x is not None:
            cv2.circle(
                frame, (int(round(lane_x)), y), 7, (0, 0, 255), -1)
            cv2.line(
                frame, (int(center_x), y), (int(round(lane_x)), y),
                (255, 255, 0), 2)

    def _select_contour(self, contours, width, height):
        minimum_area = max(80.0, width * height * 0.001)
        minimum_height = height * 0.15
        minimum_bottom = height * 0.82
        best = None
        best_score = float('-inf')

        for contour in contours:
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)
            if (area < minimum_area or h < minimum_height
                    or y + h < minimum_bottom):
                continue

            candidate_x = x + w * 0.5
            continuity_penalty = 0.0
            if self._previous_center_x is not None:
                jump = (
                    abs(candidate_x - self._previous_center_x)
                    / max(1, width))
                if jump > 0.45:
                    continue
                continuity_penalty = jump * 4.0

            area_score = area / max(1.0, width * height)
            height_score = h / max(1.0, height)
            bottom_score = (y + h) / max(1.0, height)
            score = area_score * 3.0 + height_score * 2.0 + bottom_score
            score -= continuity_penalty
            if score > best_score:
                best = contour
                best_score = score
        return best

    @staticmethod
    def _band_center(mask, y_start, y_end):
        ys, xs = np.nonzero(mask[max(0, y_start):max(0, y_end), :])
        if xs.size == 0:
            return None
        return float(np.median(xs))
