"""More robust hardware-tree row selection for the WindowHub MVP.

The previous resolver selected only the highest-scoring match for a text crop.
That is fragile for a tree because ``UR ACTIVPILOT`` is a prefix of several
rows (RC1N, RC2N, etc.). This resolver uses a clean crop from the real live
screen and deliberately chooses the TOPMOST matching row in the tree.

That matches the current MVP requirement: select the first concrete
``UR ACTIVPILOT`` entry below the group headers.
"""

from __future__ import annotations

from base64 import b64decode

import cv2
import numpy as np

from app.runtime.execution.hardware_selection_resolver import (
    HardwareSelectionResolver,
    HardwareSelectionTarget,
)


# Exact crop of the first selectable "UR ACTIVPILOT" row from the live
# WindowHub screenshot supplied during testing.  The crop is intentionally
# wider than the glyphs and includes the tree branch/indentation.
_UR_ROW_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAIAAAAARCAIAAACaZjN6AAACIklEQVR4nO2XMZKjMBBFG58FCKY4AZxAOCEi3UxkNolvMNkkyBnONlXkBHQCcwKXA6O7aANACCF7ClftyFvLCygktbrF70YCRwgBK/bY2F7A/86DBHASRYRrTU4iR6IOazNngywb52VE9dL7yrKhL2OT0JxEEWHqjIwNQUz26iLUhXJD0AcP8MMsfAPCohVCCCHalHoZmxvwigLGQCtFQieGWvTUcPMvnYciHLxdyvLSN0vkblM5nVcU0q2nxK0hjgh396P9fAkk8mjaDgGD3IsI7OdB9+5Crf4Kr25Brh+YunlFIT0kQaNKWLSjTKg0SKa5HjPQ3iDdTnRCCW5u7bPp7CuH4rdUF5VtodTD2/FqAtj5FH54em9XsS5KcJ8BXtEm8BeWmusHncjsfNImc/Jpiqta3K/hNGnS3Vuy2e12AKBen9HkXreDfn6083e417+r06HqnutlBCX4dGbA71ecoElcj6aGuP8ym+PxCADq9RndBlpjMNUUr2jTKxWfoKEVB9cfd6MFoARf76yiQa//eAZ8q/48Ir9fXyiCn+LBFjR9DH0jQaWoIXa0Q5hXtMHjadu9A+hQQK4c1ywzHd0zUBLkcS71XwI6FJD/kp84LPNy/SB5K8Qj2iKURl0BKp8Qw/i0rbSEqPEwqnoCmSLVfrSQwzWW97rnqb3Ju9o31oTRlW0csf4JW2X9E7bMmgDLrAmwzJoAy6wJsMyaAMv8AfOPZOXbgRx1AAAAAElFTkSuQmCC"
)


class HardwareTreeSelectionResolver:
    MIN_UR_CONFIDENCE = 0.58
    SCALE_FACTORS = (0.55, 0.65, 0.75, 0.85, 0.95, 1.0, 1.1, 1.2, 1.3)

    def __init__(self) -> None:
        raw = b64decode(_UR_ROW_B64)
        self._ur_row = cv2.imdecode(
            np.frombuffer(raw, dtype=np.uint8),
            cv2.IMREAD_GRAYSCALE,
        )
        if self._ur_row is None:
            raise RuntimeError("Unable to decode exact UR ACTIVPILOT row template")
        self._base = HardwareSelectionResolver()

    @staticmethod
    def _gray(image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def _topmost_match(self, image: np.ndarray):
        gray = self._gray(image)
        h, w = gray.shape[:2]

        # The hardware tree occupies the left side of the modal.  Keep the
        # search broad enough for different scaling, but exclude the document
        # table and the parts table on the right.
        x0 = int(w * 0.20)
        x1 = int(w * 0.58)
        y0 = int(h * 0.12)
        y1 = int(h * 0.72)
        region = gray[y0:y1, x0:x1]

        candidates: list[tuple[int, float, int, int, int, int]] = []
        for scale in self.SCALE_FACTORS:
            tw = max(1, int(round(self._ur_row.shape[1] * scale)))
            th = max(1, int(round(self._ur_row.shape[0] * scale)))
            if tw > region.shape[1] or th > region.shape[0]:
                continue

            resized = cv2.resize(
                self._ur_row,
                (tw, th),
                interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC,
            )
            result = cv2.matchTemplate(region, resized, cv2.TM_CCOEFF_NORMED)

            # Extract several peaks instead of only the global maximum. This
            # is the key difference: the row text is a prefix of later rows,
            # so the earliest credible match is the intended MVP entry.
            work = result.copy()
            for _ in range(8):
                _, score, _, loc = cv2.minMaxLoc(work)
                if score < self.MIN_UR_CONFIDENCE:
                    break

                rx, ry = loc
                candidates.append(
                    (
                        y0 + ry,
                        float(score),
                        x0 + rx,
                        y0 + ry,
                        tw,
                        th,
                    )
                )

                pad_x = max(4, tw // 3)
                pad_y = max(3, th // 2)
                xa = max(0, rx - pad_x)
                xb = min(work.shape[1], rx + tw + pad_x)
                ya = max(0, ry - pad_y)
                yb = min(work.shape[0], ry + th + pad_y)
                work[ya:yb, xa:xb] = -1.0

        if not candidates:
            return None

        # Prefer the first selectable row from the top.  Among nearly equal
        # y positions, prefer the stronger visual match.
        candidates.sort(key=lambda item: (item[0], -item[1]))
        return candidates[0]

    def find_ur_activpilot(self, image: np.ndarray) -> HardwareSelectionTarget | None:
        match = self._topmost_match(image)
        if match is None:
            print("[HARDWARE SELECT] exact UR row: no credible match")
            return None

        _, confidence, x, y, width, height = match
        point = (x + width // 2, y + height // 2)
        print(
            f"[HARDWARE SELECT] UR ACTIVPILOT topmost conf={confidence:.3f} "
            f"at=({x},{y},{width}x{height}) click={point}"
        )
        return HardwareSelectionTarget(
            "UR ACTIVPILOT",
            point,
            confidence,
        )

    def resolve(self, image: np.ndarray):
        ur = self.find_ur_activpilot(image)
        _, ok = self._base.resolve(image)
        return ur, ok
