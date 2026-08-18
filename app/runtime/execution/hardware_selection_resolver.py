"""WindowHub hardware dialog selector (v2).

The selector uses clean crops from the real live WindowHub dialog, but keeps
those crops isolated to the semantic text/button itself.  In particular, the
UR ACTIVPILOT template deliberately excludes the tree expand glyph at the
left of the row.  This prevents the cursor from landing on the disclosure
control instead of the selectable row.
"""

from __future__ import annotations

from base64 import b64decode
from dataclasses import dataclass

import cv2
import numpy as np


# Exact crop of the selectable text "UR ACTIVPILOT" from the live dialog.
# Crop starts at the text itself, not the tree expand control.
_UR_ACTIVPILOT_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAF8AAAAUCAYAAADr0+FaAAACi0lEQVR4nO2YMZKiQBSGP+YsQDDFCeAEaEJEuhlkI8ncYLJNYDLNNu1oEuAEcgLLQPouvYEiDQLLbFlLsPxVXWjT739//zbvqYZSSrFiEbwsLeB/xmr+gljNXxCr+Qtinvkyw/My5NCczPAMA+M+PDI5RgQgyTwDo88HUMYaj4ERZ9e1xuPw4ljLG1M+aJRknkdW9vXFlI3+yXh9q143dybbfQxpmzbgjuecfDelVgqlFKoOEdZtg0OQOYKICEGuaZSZh7GBouFRioIz9rHhTXG1PMf9nuN9bo9vbgl1TpkjCNlaPX0FbLwMae668WNyMw9LhG28KnASCy+D3Zi2nTnLtueXHdPGmbgtcwHhO4FTIVqnyAWkddcEfz9uykBitiEtZ32GcMuDDX5AVJ2pZ3GW/Ewg/bXTeHz2dQoiH3xKvoPnm19+cXBfsQZvXk0OtyZ+EFE1G5A5onKw5x2YUZi2Q3WubzIOOAOEMvuY0NdffOHkhmz7NKaNM/sDHMfL29sbAGPXWagSrKbmfbxSH3ePJw7aUmByO4FamZhryBT8gOjwRYnkcooImsdG02eJcFzfP8bL5+cnAGPXWWjqXRHBxImQuaC6G7HhwK30mDZO1e0BfwefIDpxKXOEE7QlS6/53zF+TJe8cHrCYZlXdgZEyFxQOXZ3I/7+2tCMoYYryUVFVLQNVRVN6fF5TyHpNeoynmjcI/ADh2ST4ATzu8UE21XXD/1bUElsJcP95LtQc1GnygVFM9xU1c188/q+1FXgqrTuxffWKVWoSFt3jdNyRMV4fEdPpIoOp/Z+MO9AfH9/Gkdfly5rMscfYCi1/rG2FNZfuAtiNX9BrOYviNX8BbGavyBW8xfEbwyYZe2s7biVAAAAAElFTkSuQmCC"
)

# Exact crop of the complete OK button from the live dialog.
_OK_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAFQAAAAbCAYAAADiZah4AAACZ0lEQVR4nO2ZMWgTYRSAv/ZXSBeTVqxL7XLkQGmXbrXXrUPgNocMCgaFQnA4zSAoTg6i4HA0QwkULFkzCIIHWXRpaiddGiqcZildWmm94GCl/q1Dbaq561Uk7f0t98Et/z3C4+N/7x0vXZ7n7RDTMbqjTuC0cSbocLkpueNssLi2RXNz+7hzUhIz3cPTiRSDSREa5xO63JSMz65yb+w8r3J9pBLxJfY2tyl/8Bh/scrc7YuhUrvae+iNl+tMpJNYV3uPPNGTxuM3X3j7+Ruvr184MMZ3/Rz3OzdHkkea2Enl7lgfi6tboTGB9RyXeTCphKD5I3ymxOY6TCy0wygjtFE0EEK0HqPY2HuBYRRp7AVW8wghyFejyjQcJYQ2igZ6JYsrJVJKpHQYKuj7UvcDMcw6tispZaLJ9TAUEFrleQHssoXWOstQcm2oOPs3kyp5vULWrWFpQb+jBtELbbjUR7OY7ZI0naGFJT4BUCEnTHDUlgkqCP0XFiBrTzJj5lG0dbaIXqimM7RQwWlrl7s39wppgNEsplXCteuYqk6j30QvlAz3bSjkim39sgBZkz8rXLPK2HXTP6wUInDbdNxoVg0XA10UWmeTjqSWAf5yp2HVHJaEjoFLTcGG6luOpJ6tIJ9cjiof5RGPPuI9GDjwvQIlf7rwCU0muvHipXIg3qY8NMYndLj/LFPzG0eS0Emn/L6Jme4JjfENpWmzl/HZNVI93eRGUvEqj92N/dT8OlPvNpi71R8a6xtKAMvNnzx0VnCWvsJO/KdoMiEYHjjH9LVLDCbDP4wChcb8P3E9d5hYaIeJhXaYX4Plw853Vk6dAAAAAElFTkSuQmCC"
)


@dataclass(frozen=True)
class HardwareSelectionTarget:
    name: str
    point: tuple[int, int]
    confidence: float


class HardwareSelectionResolver:
    """Find the intended selectable text row and the actual OK button."""

    SCALE_FACTORS = (0.80, 0.90, 1.00, 1.10, 1.20)
    MIN_UR_CONFIDENCE = 0.85
    MIN_OK_CONFIDENCE = 0.85

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
        region: tuple[int, int, int, int],
    ) -> tuple[float, tuple[int, int, int, int]] | None:
        gray = self._gray(image)
        h, w = gray.shape[:2]
        x1, y1, x2, y2 = region
        x1 = max(0, min(x1, w))
        x2 = max(0, min(x2, w))
        y1 = max(0, min(y1, h))
        y2 = max(0, min(y2, h))
        if x1 >= x2 or y1 >= y2:
            return None

        roi = gray[y1:y2, x1:x2]
        best = None
        for scale in self.SCALE_FACTORS:
            tw = max(1, int(round(template.shape[1] * scale)))
            th = max(1, int(round(template.shape[0] * scale)))
            if tw > roi.shape[1] or th > roi.shape[0]:
                continue
            resized = cv2.resize(
                template,
                (tw, th),
                interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC,
            )
            result = cv2.matchTemplate(roi, resized, cv2.TM_CCOEFF_NORMED)
            _, score, _, loc = cv2.minMaxLoc(result)
            candidate = (float(score), (x1 + loc[0], y1 + loc[1], tw, th))
            if best is None or candidate[0] > best[0]:
                best = candidate
        return best

    def _dialog_regions(self, image: np.ndarray) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
        h, w = image.shape[:2]
        # The hardware dialog is centered.  These broad regions are deliberately
        # large enough for normal window movement while excluding the document
        # table and the lower notes pane where false positives were found.
        tree = (
            int(w * 0.30),
            int(h * 0.27),
            int(w * 0.66),
            int(h * 0.64),
        )
        ok = (
            int(w * 0.78),
            int(h * 0.69),
            int(w * 0.98),
            int(h * 0.84),
        )
        return tree, ok

    def find_ur_activpilot(self, image: np.ndarray) -> HardwareSelectionTarget | None:
        tree_region, _ = self._dialog_regions(image)
        result = self._best_match(image, self._ur, region=tree_region)
        if result is None:
            print("[HARDWARE SELECT] UR ACTIVPILOT not found")
            return None
        confidence, (x, y, width, height) = result
        if confidence < self.MIN_UR_CONFIDENCE:
            print(f"[HARDWARE SELECT] UR ACTIVPILOT below threshold: {confidence:.3f}")
            return None

        # Click the center of the text crop itself.  The crop intentionally
        # excludes the disclosure/expand glyph, so the click cannot land on it.
        point = (x + width // 2, y + height // 2)
        print(
            f"[HARDWARE SELECT] UR ACTIVPILOT conf={confidence:.3f} "
            f"text-box=({x},{y},{width}x{height}) click={point}"
        )
        return HardwareSelectionTarget("UR ACTIVPILOT", point, confidence)

    def find_ok(self, image: np.ndarray, after: HardwareSelectionTarget | None = None) -> HardwareSelectionTarget | None:
        _, ok_region = self._dialog_regions(image)
        result = self._best_match(image, self._ok, region=ok_region)
        if result is None:
            print("[HARDWARE SELECT] OK not found")
            return None
        confidence, (x, y, width, height) = result
        if confidence < self.MIN_OK_CONFIDENCE:
            print(f"[HARDWARE SELECT] OK below threshold: {confidence:.3f}")
            return None

        point = (x + width // 2, y + height // 2)
        print(
            f"[HARDWARE SELECT] OK conf={confidence:.3f} "
            f"button-box=({x},{y},{width}x{height}) click={point}"
        )
        return HardwareSelectionTarget("OK", point, confidence)

    def resolve(self, image: np.ndarray) -> tuple[HardwareSelectionTarget | None, HardwareSelectionTarget | None]:
        return self.find_ur_activpilot(image), self.find_ok(image)
