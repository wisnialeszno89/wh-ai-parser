from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class ColorRegion:
    label: int
    x: int
    y: int
    width: int
    height: int
    area: int
    fill_ratio: float
    mean_bgr: tuple[float, float, float]
    mean_hsv: tuple[float, float, float]


@dataclass(frozen=True)
class ColorRegionObservation:
    rect: tuple[int, int, int, int]
    regions: tuple[ColorRegion, ...]


class ColorRegionObserver:
    """Extract large regular color regions from a WindowHub screenshot."""

    def observe(self, image, rect) -> ColorRegionObservation:
        analysis_rect = self._resolve_analysis_rect(image, rect)
        x, y, w, h = analysis_rect
        crop = image[y : y + h, x : x + w]
        if crop.size == 0:
            return ColorRegionObservation(analysis_rect, ())

        bgr = self._to_bgr(crop)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        # Quantize colors to suppress anti-aliasing and thin text.
        quantized = (bgr // 32).astype(np.uint8) * 32
        small = cv2.GaussianBlur(quantized, (5, 5), 0)
        compact = np.rint(small / 32.0).astype(np.uint8) * 32

        # compact is guaranteed to be HxWx3 here, regardless of screenshot input format.
        pixels = compact.reshape(-1, 3)
        colors, counts = np.unique(pixels, axis=0, return_counts=True)
        order = np.argsort(counts)[::-1]

        regions: list[ColorRegion] = []
        for color_index in order[:12]:
            color = colors[color_index]
            support = np.all(compact == color.reshape(1, 1, 3), axis=2).astype(np.uint8)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            support = cv2.morphologyEx(support, cv2.MORPH_OPEN, kernel)
            support = cv2.morphologyEx(support, cv2.MORPH_CLOSE, kernel)

            num, labels, stats, _centroids = cv2.connectedComponentsWithStats(support, 8)
            for label in range(1, num):
                area = int(stats[label, cv2.CC_STAT_AREA])
                if area < max(200, int(w * h * 0.006)):
                    continue
                rx = int(stats[label, cv2.CC_STAT_LEFT])
                ry = int(stats[label, cv2.CC_STAT_TOP])
                rw = int(stats[label, cv2.CC_STAT_WIDTH])
                rh = int(stats[label, cv2.CC_STAT_HEIGHT])
                bbox_area = max(1, rw * rh)
                fill_ratio = area / bbox_area
                if fill_ratio < 0.20:
                    continue

                mask = (labels == label).astype(np.uint8) * 255
                mean_bgr = tuple(float(v) for v in cv2.mean(bgr, mask=mask)[:3])
                mean_hsv = tuple(float(v) for v in cv2.mean(hsv, mask=mask)[:3])
                regions.append(
                    ColorRegion(
                        int(color_index * 100000 + label),
                        x + rx,
                        y + ry,
                        rw,
                        rh,
                        area,
                        fill_ratio,
                        mean_bgr,
                        mean_hsv,
                    )
                )

        regions.sort(key=lambda region: region.area, reverse=True)
        deduped: list[ColorRegion] = []
        for region in regions:
            if any(self._overlap(region, existing) > 0.70 for existing in deduped):
                continue
            deduped.append(region)
            if len(deduped) >= 24:
                break

        return ColorRegionObservation(analysis_rect, tuple(deduped))

    @classmethod
    def _resolve_analysis_rect(
        cls,
        image: np.ndarray,
        rect: tuple[int, int, int, int],
    ) -> tuple[int, int, int, int]:
        """Expand a false-small bright workspace around its center.

        The legacy workspace detector can lock onto a bright white interior and
        miss a much larger saturated construction surrounding it. When the
        proposed crop is mostly white/low-saturation, expand around its center
        and only keep the expansion if it contains meaningful color evidence.
        """
        x, y, w, h = map(int, rect)
        height, width = image.shape[:2]
        crop = cls._to_bgr(image[max(0, y):min(height, y + h), max(0, x):min(width, x + w)])
        if crop.size == 0:
            return rect

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        bright_ratio = float(np.mean(hsv[:, :, 2] > 245))
        sat_ratio = float(np.mean(hsv[:, :, 1] > 45))
        if bright_ratio < 0.78 or sat_ratio > 0.08:
            return rect

        scale = 1.80
        expanded_w = min(width, max(w, int(round(w * scale))))
        expanded_h = min(height, max(h, int(round(h * scale))))
        cx = x + w // 2
        cy = y + h // 2
        ex = max(0, min(width - expanded_w, cx - expanded_w // 2))
        ey = max(0, min(height - expanded_h, cy - expanded_h // 2))
        expanded = image[ey : ey + expanded_h, ex : ex + expanded_w]
        expanded_bgr = cls._to_bgr(expanded)
        expanded_hsv = cv2.cvtColor(expanded_bgr, cv2.COLOR_BGR2HSV)
        expanded_sat_ratio = float(np.mean(expanded_hsv[:, :, 1] > 45))

        if expanded_sat_ratio >= max(0.02, sat_ratio * 1.8):
            return (ex, ey, expanded_w, expanded_h)
        return rect

    @staticmethod
    def _to_bgr(image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        channels = image.shape[2]
        if channels == 3:
            return image
        if channels == 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        raise ValueError(f"Unsupported screenshot channel count: {channels}")

    @staticmethod
    def _overlap(a: ColorRegion, b: ColorRegion) -> float:
        ax2, ay2 = a.x + a.width, a.y + a.height
        bx2, by2 = b.x + b.width, b.y + b.height
        ix1, iy1 = max(a.x, b.x), max(a.y, b.y)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        if ix2 <= ix1 or iy2 <= iy1:
            return 0.0
        intersection = (ix2 - ix1) * (iy2 - iy1)
        return intersection / float(min(a.width * a.height, b.width * b.height))
