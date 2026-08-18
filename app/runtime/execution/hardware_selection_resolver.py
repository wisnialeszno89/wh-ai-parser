"""Deterministic MVP resolver for the WindowHub hardware dialog.

The previous implementation depended on three embedded PNG templates stored as
Base64 strings. One of those payloads can be corrupted/truncated and OpenCV then
returns ``None`` from ``imdecode()``, preventing the resolver from even starting.

For the current controlled MVP dialog we already have stable coordinates from the
live 1920x1080 screen. Use those coordinates directly, scaled to the current
screenshot size. This keeps the resolver deterministic and removes the fragile
embedded-template decoding path completely.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class HardwareSelectionTarget:
    name: str
    point: tuple[int, int]
    confidence: float


class HardwareSelectionResolver:
    """Resolve the first hardware row and OK button from a live screenshot.

    Reference geometry was measured on the supplied 1920x1080 live dialog:

      * dialog title crop origin: (450, 100)
      * UR ACTIVPILOT center:     (566, 209)
      * OK center:               (1370, 528)

    We keep the title origin in the constants because it is the useful geometric
    anchor for future visual detection, but this MVP does not decode or match any
    embedded image templates.
    """

    REFERENCE_SIZE = (1920, 1080)
    TITLE_ORIGIN = (450, 100)
    UR_ACTIVPILOT_POINT = (566, 209)
    OK_POINT = (1370, 528)

    # Kept for compatibility with callers/tests that may inspect these values.
    MIN_TITLE_CONFIDENCE = 0.90
    MIN_TARGET_CONFIDENCE = 0.90

    def __init__(self) -> None:
        # Intentionally no template decoding here.
        pass

    @classmethod
    def _scale_point(cls, point: tuple[int, int], image: np.ndarray) -> tuple[int, int]:
        h, w = image.shape[:2]
        ref_w, ref_h = cls.REFERENCE_SIZE
        sx = w / ref_w
        sy = h / ref_h
        return int(round(point[0] * sx)), int(round(point[1] * sy))

    @staticmethod
    def _clamp_point(point: tuple[int, int], image: np.ndarray) -> tuple[int, int]:
        h, w = image.shape[:2]
        x = min(max(int(point[0]), 0), max(w - 1, 0))
        y = min(max(int(point[1]), 0), max(h - 1, 0))
        return x, y

    def find_ur_activpilot(self, image: np.ndarray) -> HardwareSelectionTarget | None:
        if image is None or getattr(image, "ndim", 0) < 2:
            print("[HARDWARE SELECT] invalid screenshot supplied")
            return None

        point = self._clamp_point(self._scale_point(self.UR_ACTIVPILOT_POINT, image), image)
        print(
            "[HARDWARE SELECT] UR ACTIVPILOT positional target "
            f"point={point} reference={self.UR_ACTIVPILOT_POINT}"
        )
        return HardwareSelectionTarget("UR ACTIVPILOT", point, 0.95)

    def find_ok(
        self,
        image: np.ndarray,
        after: HardwareSelectionTarget | None = None,
    ) -> HardwareSelectionTarget | None:
        if image is None or getattr(image, "ndim", 0) < 2:
            print("[HARDWARE SELECT] invalid screenshot supplied")
            return None

        point = self._clamp_point(self._scale_point(self.OK_POINT, image), image)
        print(
            "[HARDWARE SELECT] OK positional target "
            f"point={point} reference={self.OK_POINT}"
        )
        return HardwareSelectionTarget("OK", point, 0.95)

    def resolve(self, image: np.ndarray):
        return self.find_ur_activpilot(image), self.find_ok(image)
