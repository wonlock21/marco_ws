"""Turuncu renk maskesi ve geometri ile serit algilama."""

import cv2
import numpy as np

def _hybrid_orange_lane_mask(
        frame, hue_min=1, hue_max=25, sat_min=80, val_min=80,
        minimum_pixel_ratio=0.01, sobel_threshold=40, use_umat=False):
    """HSV turuncu maskesi uret; renk kaybolursa Sobel'e geri dus."""
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError('turuncu serit maskesi 3 kanalli BGR kare bekler')
    if not 0 <= int(hue_min) <= int(hue_max) <= 179:
        raise ValueError('HSV hue sinirlari 0..179 araliginda olmali')
    if not 0 <= int(sat_min) <= 255 or not 0 <= int(val_min) <= 255:
        raise ValueError('HSV doygunluk ve parlaklik sinirlari 0..255 olmali')
    if not 0.0 <= float(minimum_pixel_ratio) <= 1.0:
        raise ValueError('minimum_pixel_ratio 0..1 araliginda olmali')

    source = cv2.UMat(frame) if use_umat else frame
    blurred = cv2.GaussianBlur(source, (5, 5), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    lower = np.array([hue_min, sat_min, val_min], dtype=np.uint8)
    upper = np.array([hue_max, 255, 255], dtype=np.uint8)
    hsv_mask = cv2.inRange(hsv, lower, upper)

    cleaned_hsv = cv2.erode(
        hsv_mask, np.ones((3, 3), np.uint8), iterations=1)
    cleaned_hsv = cv2.dilate(
        cleaned_hsv, np.ones((7, 7), np.uint8), iterations=2)

    total_pixels = int(frame.shape[0] * frame.shape[1])
    if cv2.countNonZero(cleaned_hsv) < (
            total_pixels * float(minimum_pixel_ratio)):
        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
        sobel_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        magnitude = cv2.magnitude(sobel_x, sobel_y)
        magnitude_uint8 = cv2.convertScaleAbs(magnitude)
        _, edge_mask = cv2.threshold(
            magnitude_uint8, int(sobel_threshold), 255, cv2.THRESH_BINARY)
        sobel_mask = cv2.morphologyEx(
            edge_mask, cv2.MORPH_CLOSE, np.ones((5, 45), np.uint8))
        result = cv2.morphologyEx(
            sobel_mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    else:
        result = cleaned_hsv
    return result.get() if isinstance(result, cv2.UMat) else result


def hybrid_orange_lane_mask_opencl(
        frame, hue_min=0, hue_max=25, sat_min=80, val_min=80,
        minimum_pixel_ratio=0.01, sobel_threshold=40):
    """OpenCV T-API ile OpenCL hizlandirmali hibrit turuncu maske."""
    return _hybrid_orange_lane_mask(
        frame, hue_min, hue_max, sat_min, val_min,
        minimum_pixel_ratio, sobel_threshold, use_umat=True)


def hybrid_orange_lane_mask_cpu(
        frame, hue_min=0, hue_max=25, sat_min=80, val_min=80,
        minimum_pixel_ratio=0.01, sobel_threshold=40):
    """OpenCL kullanilamadiginda ayni hibrit maskeyi CPU'da uygula."""
    return _hybrid_orange_lane_mask(
        frame, hue_min, hue_max, sat_min, val_min,
        minimum_pixel_ratio, sobel_threshold, use_umat=False)


class LaneDetector:
    def __init__(
            self, use_opencl=False, orange_hue_min=0, orange_hue_max=25,
            orange_sat_min=80, orange_val_min=80,
            orange_min_pixel_ratio=0.01, sobel_threshold=40,
            ipm_enabled=False, ipm_source_points=None,
            ipm_destination_points=None, lookahead_y=160,
            lookahead_band_half_height=5):
        self.use_opencl = use_opencl
        self.orange_hue_min = int(orange_hue_min)
        self.orange_hue_max = int(orange_hue_max)
        self.orange_sat_min = int(orange_sat_min)
        self.orange_val_min = int(orange_val_min)
        self.orange_min_pixel_ratio = float(orange_min_pixel_ratio)
        self.sobel_threshold = int(sobel_threshold)
        self.ipm_enabled = bool(ipm_enabled)
        self.ipm_source_points = ipm_source_points or [
            0.20, 0.95, 0.42, 0.45, 0.58, 0.45, 0.80, 0.95]
        self.ipm_destination_points = ipm_destination_points or [
            0.20, 1.00, 0.20, 0.00, 0.80, 0.00, 0.80, 1.00]
        self.lookahead_y = int(lookahead_y)
        self.lookahead_band_half_height = max(
            1, int(lookahead_band_half_height))
        self.last_mask = None
        self.last_raw_mask = None
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
            mask = hybrid_orange_lane_mask_opencl(
                working_frame,
                hue_min=self.orange_hue_min,
                hue_max=self.orange_hue_max,
                sat_min=self.orange_sat_min,
                val_min=self.orange_val_min,
                minimum_pixel_ratio=self.orange_min_pixel_ratio,
                sobel_threshold=self.sobel_threshold)
        else:
            mask = hybrid_orange_lane_mask_cpu(
                working_frame,
                hue_min=self.orange_hue_min,
                hue_max=self.orange_hue_max,
                sat_min=self.orange_sat_min,
                val_min=self.orange_val_min,
                minimum_pixel_ratio=self.orange_min_pixel_ratio,
                sobel_threshold=self.sobel_threshold)
        self.last_raw_mask = mask

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        selected = self._select_contour(contours, width, height)
        if selected is None:
            self.last_mask = np.zeros_like(mask)
            self.last_selected_mask = np.zeros_like(mask)
            self.last_heading_error = 0.0
            self.last_confidence = 0.0
            self.last_lookahead_x = None
            self._draw_lookahead(working_frame, center_x, None)
            return False, 0.0

        selected_mask = np.zeros_like(mask)
        cv2.drawContours(selected_mask, [selected], -1, 255, -1)
        selected_mask = self._clean_lane_body(selected_mask)
        clean_contours, _ = cv2.findContours(
            selected_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if clean_contours:
            selected = max(clean_contours, key=cv2.contourArea)
        self.last_mask = selected_mask
        self.last_selected_mask = selected_mask
        band_near_x = self._band_center(
            selected_mask, int(height * 0.72), height)
        band_far_x = self._band_center(
            selected_mask, int(height * 0.40), int(height * 0.68))

        moments = cv2.moments(selected)
        contour_x = (
            float(moments['m10'] / moments['m00'])
            if moments['m00'] > 0.0 else float(center_x))
        near_y = int(height * 0.84)
        far_y = int(height * 0.54)
        fitted_centers = self._fit_contour_axis(
            selected, width, near_y, far_y)
        if band_near_x is not None and band_far_x is not None:
            near_x, far_x = band_near_x, band_far_x
        elif fitted_centers is not None:
            near_x, far_x = fitted_centers
        else:
            near_x = band_near_x if band_near_x is not None else contour_x
            far_x = band_far_x if band_far_x is not None else contour_x

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
        cv2.line(
            working_frame, (int(center_x), 0),
            (int(center_x), height - 1), (255, 0, 0), 2)

        return True, float(near_x - center_x)

    @staticmethod
    def _clean_lane_body(component_mask):
        """Serit govdesini doldur, kisa yatay leke cikintilarini ayikla."""
        height, width = component_mask.shape[:2]
        rows = []
        for y in range(height):
            xs = np.flatnonzero(component_mask[y])
            if xs.size:
                rows.append((y, int(xs[0]), int(xs[-1])))
        if len(rows) < max(8, int(height * 0.12)):
            return component_mask

        widths = np.asarray(
            [right - left + 1 for _, left, right in rows], dtype=np.float32)
        # Bagli zemin lekesi goruntunun uzun bir bolumunde seridi genisletebilir.
        # Medyan bu durumda lekenin genisligini "normal" kabul eder. Alt
        # yuzdelik, gercek seridin en az bir temiz dikey parcasi kaldigi surece
        # govde genisligini korur.
        typical_width = float(np.percentile(widths, 30.0))
        if typical_width <= 0.0:
            return component_mask

        # Zemindeki kisa cizgiler seride baglandiginda yalnizca birkac satiri
        # asiri genisletir. Satir genisligi medyanindan sapan bu satirlari
        # atip iki serit kenarini kalan satirlardan yeniden kuruyoruz.
        max_width = min(
            width * 0.45,
            max(typical_width * 1.35, typical_width + 10.0))
        min_width = max(2.0, typical_width * 0.35)
        valid = [
            row for row, row_width in zip(rows, widths)
            if min_width <= float(row_width) <= max_width
        ]
        # Uzun bir leke satirlarin yaridan fazlasini bozsa bile ust/alt temiz
        # parcalar eksen ve genisligi yeniden kurmak icin yeterlidir.
        if len(valid) < max(8, int(height * 0.12)):
            return component_mask

        ys = np.asarray([row[0] for row in valid], dtype=np.float32)
        lefts = np.asarray([row[1] for row in valid], dtype=np.float32)
        rights = np.asarray([row[2] for row in valid], dtype=np.float32)
        all_y = np.arange(int(ys[0]), int(ys[-1]) + 1, dtype=np.float32)
        left_interp = np.interp(all_y, ys, lefts)
        right_interp = np.interp(all_y, ys, rights)

        # Kisa yatay derz/zemin izleri birkac ardışık satir boyunca serit
        # kenarini disari cekebilir. Daha uzun uzamsal medyan, bu darbeleri
        # temizlerken seridin yavas degisen egimini korur.
        smooth_window = min(31, len(all_y))
        if smooth_window >= 3:
            if smooth_window % 2 == 0:
                smooth_window -= 1
            half = smooth_window // 2

            def rolling_median(values):
                padded = np.pad(values, (half, half), mode='edge')
                windows = np.lib.stride_tricks.sliding_window_view(
                    padded, smooth_window)
                return np.median(windows, axis=1).astype(np.float32)

            left_interp = rolling_median(left_interp)
            right_interp = rolling_median(right_interp)

        result = np.zeros_like(component_mask)
        for y_value, left, right in zip(all_y, left_interp, right_interp):
            x0 = max(0, min(width - 1, int(round(left))))
            x1 = max(x0, min(width - 1, int(round(right))))
            result[int(y_value), x0:x1 + 1] = 255
        return result

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

            bottom_start = max(y, int(height * 0.72))
            candidate_mask = np.zeros((height, width), dtype=np.uint8)
            cv2.drawContours(candidate_mask, [contour], -1, 255, -1)
            candidate_x = self._band_center(
                candidate_mask, bottom_start, height)
            if candidate_x is None:
                continue
            continuity_penalty = 0.0
            if self._previous_center_x is not None:
                jump = (
                    abs(candidate_x - self._previous_center_x)
                    / max(1, width))
                if jump > 0.22:
                    continue
                continuity_penalty = jump * 7.0

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

    @staticmethod
    def _fit_contour_axis(contour, width, near_y, far_y):
        """Secili seridin ana eksenini uydurup iki y satirindaki x'i bul."""
        points = np.asarray(contour, dtype=np.float32).reshape(-1, 2)
        if points.shape[0] < 2:
            return None
        vx, vy, x0, y0 = cv2.fitLine(
            points, cv2.DIST_L2, 0, 0.01, 0.01).reshape(-1)
        if abs(float(vy)) < 1e-3:
            return None

        slope = float(vx) / float(vy)

        def x_at(y):
            value = float(x0) + (float(y) - float(y0)) * slope
            return max(0.0, min(float(width - 1), value))

        return x_at(near_y), x_at(far_y)
