from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class BoundaryCandidate:
    orientation: str
    coordinate: int
    strength: float


@dataclass(frozen=True)
class ColorBoundaryObservation:
    vertical: tuple[BoundaryCandidate, ...]
    horizontal: tuple[BoundaryCandidate, ...]


class ColorBoundaryObserver:
    """Find thin or broad construction separators directly from pixels.

    The key distinction from the first implementation is that separators are
    not estimated from a median color profile. A thin mullion can occupy only
    a few pixels in each column and therefore disappear in a median. We instead
    score local per-row/per-column transitions and aggregate them robustly.
    """

    def observe(self, image, rect) -> ColorBoundaryObservation:
        x, y, w, h = rect
        crop = image[y : y + h, x : x + w]
        if crop.size == 0:
            return ColorBoundaryObservation((), ())

        if crop.ndim == 2:
            bgr = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)
        else:
            bgr = crop

        vertical = self._profile(bgr, "vertical")
        horizontal = self._profile(bgr, "horizontal")
        return ColorBoundaryObservation(tuple(vertical), tuple(horizontal))

    @staticmethod
    def _profile(bgr: np.ndarray, orientation: str) -> list[BoundaryCandidate]:
        height, width = bgr.shape[:2]
        # Avoid the outer frame bevel and toolbar-adjacent noise. The interior
        # construction content is what we want to classify.
        y0, y1 = int(height * 0.18), int(height * 0.82)
        x0, x1 = int(width * 0.18), int(width * 0.82)

        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)

        if orientation == "vertical":
            strip = gray[y0:y1, :]
            sat = hsv[y0:y1, :, 1] / 255.0
            # Adjacent-column transition for every row. Thin vertical members
            # therefore survive the aggregation instead of being median-washed.
            diff = np.linalg.norm(
                bgr[y0:y1, 1:].astype(np.float32) - bgr[y0:y1, :-1].astype(np.float32),
                axis=2,
            ) / 441.67
            dark = (strip < 90.0).astype(np.float32)
            sat_jump = np.abs(np.diff(sat, axis=1))
            axis_score = self._aggregate_rows(diff, dark[:, 1:], sat_jump)
            lo, hi = x0, x1
            coordinate_offset = 1
        else:
            strip = gray[:, x0:x1]
            sat = hsv[:, x0:x1, 1] / 255.0
            diff = np.linalg.norm(
                bgr[1:, x0:x1].astype(np.float32) - bgr[:-1, x0:x1].astype(np.float32),
                axis=2,
            ) / 441.67
            dark = (strip < 90.0).astype(np.float32)
            sat_jump = np.abs(np.diff(sat, axis=0))
            axis_score = self._aggregate_columns(diff, dark[1:, :], sat_jump)
            lo, hi = y0, y1
            coordinate_offset = 1

        if axis_score.size < 15:
            return []

        smooth = cv2.GaussianBlur(
            axis_score.reshape(1, -1).astype(np.float32),
            (1, 5),
            0,
        ).ravel()

        local = smooth[lo : hi - 1]
        if local.size == 0:
            return []

        median = float(np.median(local))
        mad = float(np.median(np.abs(local - median))) + 1e-6
        robust_threshold = median + max(0.08, 5.0 * mad)
        peak = float(np.max(local))
        threshold = min(0.70, max(0.10, robust_threshold, peak * 0.32))

        candidates: list[BoundaryCandidate] = []
        for index in range(lo + 2, hi - 2):
            value = float(smooth[index])
            if value < threshold:
                continue
            neighborhood = smooth[index - 2 : index + 3]
            if value < float(np.max(neighborhood)):
                continue
            coordinate = index + coordinate_offset
            if any(abs(c.coordinate - coordinate) <= 7 for c in candidates):
                continue
            candidates.append(
                BoundaryCandidate(
                    orientation,
                    coordinate,
                    min(1.0, value),
                )
            )

        candidates.sort(key=lambda c: c.strength, reverse=True)
        return sorted(candidates[:8], key=lambda c: c.coordinate)

    @staticmethod
    def _aggregate_rows(diff: np.ndarray, dark: np.ndarray, sat_jump: np.ndarray) -> np.ndarray:
        # A real separator affects a large fraction of rows. Text or labels do
        # not, so percentile + dark/saturation support is more stable than mean.
        base = np.percentile(diff, 82, axis=0)
        dark_support = np.mean(dark, axis=0)
        sat_support = np.percentile(sat_jump, 75, axis=0)
        return np.clip(0.70 * base + 0.20 * dark_support + 0.10 * sat_support, 0.0, 1.5)

    @staticmethod
    def _aggregate_columns(diff: np.ndarray, dark: np.ndarray, sat_jump: np.ndarray) -> np.ndarray:
        base = np.percentile(diff, 82, axis=1)
        dark_support = np.mean(dark, axis=1)
        sat_support = np.percentile(sat_jump, 75, axis=1)
        return np.clip(0.70 * base + 0.20 * dark_support + 0.10 * sat_support, 0.0, 1.5)
