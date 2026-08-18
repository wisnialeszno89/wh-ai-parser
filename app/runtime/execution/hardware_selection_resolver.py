"""Semantic MVP selector for the WindowHub hardware-selection dialog.

The first version deliberately uses text-row/button image anchors rather than
hard-coded screen coordinates.  The anchors were cropped from the real
WindowHub dialog shown during live testing:

    UR ACTIVPILOT
    OK

The resolver searches the current screenshot at several scales and returns
screen-local click points.  This keeps the selector independent of the
current dialog position and gives us a clean seam to replace the image anchors
with OCR/UI semantics later.
"""

from __future__ import annotations

from base64 import b64decode
from dataclasses import dataclass

import cv2
import numpy as np


# Clean crop of the selectable tree row text "UR ACTIVPILOT".
_UR_ACTIVPILOT_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAHUAAAAKCAYAAACKcBGoAAACDUlEQVR4nO2WPXKjQBCFP3QWROCaE3ADpISIdLNRJpP4Bs42wcqkbFMiJ8AJlhOoFGi4S2+AsAcEGG9p15RLr4qi5qcfj+75ecgQTCK+n4jp6+uOmUR8tOSjXFq070ti7G5f6MTl2mqPaagbkticQ/pyLTRte6yPv9HV6s9Fg/ht8b2xc8CCW8D1UCPDVZZC9ESoStKsanrJUkjMnsCaG+zb7Q8+zDrindOcIFrjdqcFIbo8YSZxFvyMIfn1aPEE7E0CaUY1GDcf3KaoxSsH/4Fl72BdvGjtEoSasklMlZGWCu+qAp+D6ynKk7nIOKB6CKuX5xF93clnjn7EukvjeqjJC+NrsQDYbrfY70koY5aOg+M4OM8PmN+P1zsE6uJxSVIQosuUt806NdFjCEL04ZWCivNREzbb3NK3TKNhfd8QC4Ddbof9ngQ/wYgguYaRFVxlKeVbglccuBzBroeyC/zXCAj1kXORkarw/ehu9IkgnynokK7qzPEWi/A/YPj47fm5KksplddOULBHclg5G4orkoosLdH5JbmXRVAfwQFPCcTLdlyx6eMZRxAq4lWMCqffxiNsta4fL9b9WbBZxv339RwxaqNMIj4IzTPiGmsn23a3/Q4xF23Nq+Osb+h8OL6lx3bNuWg+cM198d3/szi6unTX2s/Y/ToiIl+znO74V7iN+71jVrgX9RviDyQIwL8B1L9UAAAAAElFTkSuQmCC"
)

# Clean crop of the real WindowHub OK button.
_OK_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAFAAAAAjCAYAAAADp43CAAACuklEQVR4nO2aP2gTURjAf8lFSDuYNDYVSu0SElDapVvtdesQuM0hg4JBoRAcTjMIipODKDiEZigFwZI1gyB4kEWXpnbSpaHCaZZSAq1tvOBgbe9Sh9rrv6uCh7kLvB/ckPc9wseP773v8XgBwzD2EPwzQa8T6HaEQJcIgS4RAl0iBLpECHRJ6OiP1ZbFHa3J8sYure22Vzn5CiXZw9OpKMMRyTFuC1xtWUzOr3Nv4gKvszGiYVGcxnab0keDyZfrLNy+6CgxcHCQvvFqi6lkBPVqX8cT9TuP337l3ZfvvLkePxWzy0zTf3BzLNLRxLqFuxMxltd3HWPH1qlYts5EwxKtn849QRhziRDoEs8F1osykiTZn1ysHwSQ5SL1g4mVHJIkkat4lakzngqsF2VS5Qy6ZWFZFpalMZJPHUo8nIis1CjoFnNpb3I9Cw8FVnieh0JJJWGPpZnTC1DWDiuPCrlUmYxeRU04/Y+3eCewrlMbz6CclJJIMbK0wmcAymQlBTR/ygMf7IF/ZAkyhWleKDl8tvXZeCcwkWJkqYx2Yrvbr8wrJAHGMyjqHHqhhuK37vEbDyswzf0C5LPFE/tdHjIKR1dsQi1RqCmnm4sPCP19yv8joVbRkUlJeXtsWrOopoFjrhKoVY0VKYWMTtVHG6J9mRB9tob15LLX+fgW6dEnjAdDp8b93US6AFtgJBzEEJeojhjb1pkxW+DowDlmFpsdSajbKH1ooSR7HGN2E5lV+pic3yDaEyQ7FhVXW+zfSM8sbjHzvsnCrQHHOYGjTztWWyYPtTW0lW+wJ158RMISo0Pnmb12ieGI84ElIN7GuEOsU5cIgS4RAl0iBLrkWGsxTZPNzU12dnZot8WhGqC3t5dYLEYo5NyF7VHTNGk0GsTjcfr7+wkGRXG2222azSaNRoPBwUFHib8AuCLe2SPtldwAAAAASUVORK5CYII="
)


@dataclass(frozen=True)
class HardwareSelectionTarget:
    name: str
    point: tuple[int, int]
    confidence: float


class HardwareSelectionResolver:
    """Find semantic MVP targets in the currently visible dialog."""

    SCALE_FACTORS = (0.75, 0.85, 0.95, 1.0, 1.05, 1.15, 1.25, 1.35)
    MIN_UR_CONFIDENCE = 0.72
    MIN_OK_CONFIDENCE = 0.78

    def __init__(self) -> None:
        self._ur = self._decode(_UR_ACTIVPILOT_B64)
        self._ok = self._decode(_OK_B64)

    @staticmethod
    def _decode(payload: str) -> np.ndarray:
        raw = b64decode(payload)
        image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise RuntimeError("Unable to decode embedded hardware selection template")
        return image

    @staticmethod
    def _gray(image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def _best_match(
        self,
        image: np.ndarray,
        template: np.ndarray,
        *,
        min_y: int = 0,
        min_x: int = 0,
        max_x: int | None = None,
        max_y: int | None = None,
    ) -> tuple[float, tuple[int, int, int, int]] | None:
        gray = self._gray(image)
        h_img, w_img = gray.shape[:2]
        max_x = w_img if max_x is None else min(max_x, w_img)
        max_y = h_img if max_y is None else min(max_y, h_img)
        min_x = max(0, min_x)
        min_y = max(0, min_y)

        if min_x >= max_x or min_y >= max_y:
            return None

        region = gray[min_y:max_y, min_x:max_x]
        best: tuple[float, tuple[int, int, int, int]] | None = None

        for scale in self.SCALE_FACTORS:
            width = max(1, int(round(template.shape[1] * scale)))
            height = max(1, int(round(template.shape[0] * scale)))
            if width > region.shape[1] or height > region.shape[0]:
                continue

            resized = cv2.resize(
                template,
                (width, height),
                interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC,
            )
            result = cv2.matchTemplate(region, resized, cv2.TM_CCOEFF_NORMED)
            _, confidence, _, location = cv2.minMaxLoc(result)
            x, y = location
            candidate = (float(confidence), (min_x + x, min_y + y, width, height))
            if best is None or candidate[0] > best[0]:
                best = candidate

        return best

    def find_ur_activpilot(self, image: np.ndarray) -> HardwareSelectionTarget | None:
        # UR ACTIVPILOT belongs to the left tree. Restrict the search to the
        # left side of the modal so unrelated text elsewhere cannot win.
        result = self._best_match(
            image,
            self._ur,
            min_x=int(image.shape[1] * 0.28),
            max_x=int(image.shape[1] * 0.72),
            min_y=int(image.shape[0] * 0.18),
            max_y=int(image.shape[0] * 0.80),
        )
        if result is None or result[0] < self.MIN_UR_CONFIDENCE:
            score = 0.0 if result is None else result[0]
            print(f"[HARDWARE SELECT] UR ACTIVPILOT below threshold: {score:.3f}")
            return None

        confidence, (x, y, width, height) = result
        point = (x + width // 2, y + height // 2)
        print(
            f"[HARDWARE SELECT] UR ACTIVPILOT conf={confidence:.3f} "
            f"at=({x},{y},{width}x{height}) click={point}"
        )
        return HardwareSelectionTarget("UR ACTIVPILOT", point, confidence)

    def find_ok(self, image: np.ndarray, after: HardwareSelectionTarget | None = None) -> HardwareSelectionTarget | None:
        # OK is in the lower-right area of the modal. Search there first.
        result = self._best_match(
            image,
            self._ok,
            min_x=int(image.shape[1] * 0.65),
            max_x=int(image.shape[1] * 0.99),
            min_y=int(image.shape[0] * 0.55),
            max_y=int(image.shape[0] * 0.97),
        )
        if result is None or result[0] < self.MIN_OK_CONFIDENCE:
            score = 0.0 if result is None else result[0]
            print(f"[HARDWARE SELECT] OK below threshold: {score:.3f}")
            return None

        confidence, (x, y, width, height) = result
        point = (x + width // 2, y + height // 2)
        print(
            f"[HARDWARE SELECT] OK conf={confidence:.3f} "
            f"at=({x},{y},{width}x{height}) click={point}"
        )
        return HardwareSelectionTarget("OK", point, confidence)

    def resolve(self, image: np.ndarray) -> tuple[HardwareSelectionTarget | None, HardwareSelectionTarget | None]:
        return self.find_ur_activpilot(image), self.find_ok(image)
