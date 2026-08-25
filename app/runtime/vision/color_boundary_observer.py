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
    """Find broad color transitions inside a WindowHub construction crop."""

    def observe(self, image, rect) -> ColorBoundaryObservation:
        x, y, w, h = rect
        crop = image[y : y + h, x : x + w]
        if crop.size == 0:
            return ColorBoundaryObservation((), ())

        if crop.ndim == 2:
            bgr = cv2.cvtColor(crop, cv2.COLOR_GRAY2BGR)
        else:
            bgr = crop
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)

        vertical = self._profile(bgr, hsv, "vertical")
        horizontal = self._profile(bgr, hsv, "horizontal")
        return ColorBoundaryObservation(tuple(vertical), tuple(horizontal))

    @staticmethod
    def _profile(bgr: np.ndarray, hsv: np.ndarray, orientation: str) -> list[BoundaryCandidate]:
        height, width = bgr.shape[:2]
        y0, y1 = int(height * 0.14), int(height * 0.86)
        x0, x1 = int(width * 0.14), int(width * 0.86)

        if orientation == "vertical":
            sample = bgr[y0:y1]
            profile = np.median(sample.astype(np.float32), axis=0)
        else:
            sample = bgr[:, x0:x1]
            profile = np.median(sample.astype(np.float32), axis=1)

        delta = np.linalg.norm(np.diff(profile, axis=0, prepend=profile[:1]), axis=1) / 255.0
        if delta.size < 15:
            return []

        smooth = cv2.GaussianBlur(delta.reshape(1, -1).astype(np.float32), (1, 11), 0).ravel()
        lo, hi = int(len(smooth) * 0.10), int(len(smooth) * 0.90)
        peak = float(np.max(smooth[lo:hi]))
        if peak < 0.08:
            return []

        candidates: list[BoundaryCandidate] = []
        threshold = max(0.08, peak * 0.30)
        for i in range(lo + 3, hi - 3):
            value = float(smooth[i])
            if value < threshold:
                continue
            local = smooth[i - 3 : i + 4]
            if value < float(np.max(local)):
                continue
            if any(abs(c.coordinate - i) <= 10 for c in candidates):
                continue
            candidates.append(BoundaryCandidate(orientation, i, min(1.0, value)))

        candidates.sort(key=lambda c: c.strength, reverse=True)
        return sorted(candidates[:8], key=lambda c: c.coordinate)
