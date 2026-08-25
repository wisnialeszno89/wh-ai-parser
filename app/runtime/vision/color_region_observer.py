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
    """Extract large regular color regions from a WindowHub workspace screenshot."""

    def observe(self, image, rect) -> ColorRegionObservation:
        x, y, w, h = rect
        crop = image[y : y + h, x : x + w]
        if crop.size == 0:
            return ColorRegionObservation(rect, ())

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
        for color_index in order[:10]:
            color = colors[color_index]
            support = np.all(compact == color.reshape(1, 1, 3), axis=2).astype(np.uint8)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            support = cv2.morphologyEx(support, cv2.MORPH_OPEN, kernel)
            support = cv2.morphologyEx(support, cv2.MORPH_CLOSE, kernel)

            num, labels, stats, _centroids = cv2.connectedComponentsWithStats(support, 8)
            for label in range(1, num):
                area = int(stats[label, cv2.CC_STAT_AREA])
                if area < max(200, int(w * h * 0.01)):
                    continue
                rx = int(stats[label, cv2.CC_STAT_LEFT])
                ry = int(stats[label, cv2.CC_STAT_TOP])
                rw = int(stats[label, cv2.CC_STAT_WIDTH])
                rh = int(stats[label, cv2.CC_STAT_HEIGHT])
                bbox_area = max(1, rw * rh)
                fill_ratio = area / bbox_area
                if fill_ratio < 0.20:
                    continue

                mask = labels == label
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
            if len(deduped) >= 20:
                break

        return ColorRegionObservation(rect, tuple(deduped))

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
