from __future__ import annotations

import base64
from dataclasses import dataclass

import cv2
import numpy as np


# Real WindowHub UI crops captured from the hardware-selection dialog.
# These are wider than text-only glyph crops so matching also uses UI chrome.
_TITLEBAR_TEMPLATE_B64 = "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"
_UR_ROW_TEMPLATE_B64 = "iVBORw0KGgoAAAANSUhEUgAAAGkAAAAUCAIAAAABXIRyAAAD+klEQVRYCe3BIXYb+w4H4N9/L5oLfLqCaAWTS4JKxTyo0ZCyQLNLLLMpEw0KeZ4VyCvoCehoL3rOpO1rb08ecKi/r1UVri7SqgpXF2lVhauLtKrC1UVaVeHqIq2q8JY0FngoYZXGAndIN57w6ma/hBL+kMbdiP0SSvhhHtrtF7za7vdfx/GEX91st/jy5YSz7XHZ7AQeSjhLY8HDx8fb8YRX22NNfRp34wln2+Oy2Qk8lPA/adyNJ6xu9ksojLvxhF/d7JdQwkVaVeEtaSzwUMIqjQXuEIGHEoA07p4faurxuzSW5w/4uvFQwlkad+OHY009XszDgGnqAaSxwEMJqzQWeCghjQUeSkAaC9whAg8lAPPQdpsllNJY4KGUxgIPJXyXxt3jxyWUcDYP7fbrfgklnKWxwEMJ79KqCm9JY4GHElZpLHCHCDyUcDYP7emuph6/SWOBPzx3u80SSkAaCzyU8G9pLPBQwiqNBR5KQBoLPJQwD/ztc/z9HxZ4KOFsHtrTXU19Ggs8lNJY4KGEV/PQdpsllPBdGgs8lACkscBDCe/SqgpvSWOBhxJWaSxwhwg8lADMQ9ttllDCr9JY4KHL0HabJZTSuHt+qKnHH9JY4KGEVRoLPJQAzEN7uqupn4f2dFdTZyzwUALSuHv8uIRSGgs8lNJY4KGEVRoLPJTw0zy0p7uaegBpLPBQwru0T58+HQ6H+/v7w+Fwf39/OBzu7+8PhwPO0ljgoYRVGgvcId14wupmv4QSfpfGAg8lzEPbbZZQGAs8lPCHNBZ4KGGVxgIPJZzNQ3u6q8/f+J+/YurTuBtPWN3sl1ACkMYCD6U0FngoYZXGAg8l/DQP7emuph5AGgs8lPAurarwljQWeChhlcYCd4jAQ2ke2i2ONfX4TRp34wk/3OyX0GVou80SSvi3NBZ4KGGVxgIPJbyYB/529/Hx6a+YeqSxwEMJv0hjgYdSGgs8lPBqHtpus4QSvktjgYcSgDQWeCjhXVpV4U3z0HabJZRwlsbd80N9/sYCDyUA89Bucaypx09p3D0/1NTjxTy03WYJhXE3fjjW1OPFPAyYph5AGgs8lLBKY4GHElbz0G6/bI819UAaCzyU8Is0FngopbHAQwnfpXH3+HEJJZzNQ7v9ul9CCWdpLPBQwru0qsL/kcbdeMLqZr+EUhoLPJTwIo27EfsllPAijQUeSng1D223WUIJadyNJ7zaHmvqcZbGAg8lAGncjSecbY819Tibh/Z0V1MPII0FHkr4IY278YSz7XHZ7LrxhFfbY009kMbdeMJqe6ypx3dpLPBQwru0qsLVRVpV4eoirapwdZFWVbi6SKsqXF2kVRWuLtKqClcX+S8w7Fr3vTgarwAAAABJRU5ErkJggg=="
_OK_TEMPLATE_B64 = "iVBORw0KGgoAAAANSUhEUgAAADQAAAAaCAIAAAB3vOj6AAACN0lEQVRIDc3Bv2sTUQAH8O/LLZn0+Wt2OHtyoZOb9bpYh0AcOmVxuKlwODzM4CAoXXJw4BC5KeBQbnHIIF0O7g94kD/A0OHgHMJDsFL9ZhPss5ZQurR1SuF9PoIkXCVIwlWCJJbmC/uy/Pnl8M/i91+4QZAEMF/Yzbvvr57cURu3ZbsFNwiSAF58Pnq2dlNt3IJLBEkAMjNH7x7KdgsuESQByMzYNIRjBEkAMjM2DeEYQRKAzIxNQzhGkAQgM2PTENegyaNgMMXS41GtlY8mj2IUWvkAqsTrfdwp7biLiwRJADIzNg2xak0eBZN+rZWPU1Xi9WajWvfKKEahld/kUTDp11r5uJQgCUBmxqYhVqxKvGGn1srHmSaPYhQF4hiFDt57w06tlY+rCJIAZGZsGmK1mjyKUWjl41yVePvbdWcYTzCdrpd23MV/CJIAZGZsGmK1mjyKUWjl41yVePvbdWcYTPqj9cEApR13cSVBEoDMjE1DrFiVeMNOrZWPM00exSgKxDEKrZBHwcFbO+7iCoIkAJkZm4ZYtSaPgkm/1srHqSrxerNRrXtlFKPQykeTR8GkX2vl4zKCJACZGZuGuAZNHgWDKZZ2SjvuAk0exSi08nGqSrzebFRr5eMCQRKAzIxNQzhGkAQgM2PTEI4RJAHc//Dt6+s12W7BJYIkgOeffjx9cGN36y5cIkgCmC+ON/cOd7fuxY+kbLfgBkESS/PF8ZvSlAe/cHICNwiScJUgCVcJknDVP2zCFgTI39H6AAAAAElFTkSuQmCC"


@dataclass(frozen=True, slots=True)
class HardwareDialogLayout:
    x: int
    y: int
    width: int
    height: int
    ur_activation_point: tuple[int, int]
    ok_button_point: tuple[int, int]

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def tree_region(self) -> tuple[int, int, int, int]:
        return (
            self.x + int(self.width * 0.02),
            self.y + int(self.height * 0.08),
            int(self.width * 0.48),
            int(self.height * 0.52),
        )

    @property
    def parts_region(self) -> tuple[int, int, int, int]:
        return (
            self.x + int(self.width * 0.52),
            self.y + int(self.height * 0.08),
            int(self.width * 0.42),
            int(self.height * 0.34),
        )

    @property
    def first_tree_item_point(self) -> tuple[int, int]:
        return self.ur_activation_point

    @property
    def ok_point(self) -> tuple[int, int]:
        return self.ok_button_point


class HardwareDialogResolver:
    """Resolve the WindowHub hardware-selection modal semantically."""

    _TITLE_SCALES = (0.85, 0.90, 0.95, 1.0, 1.05, 1.10, 1.15)
    _DEFAULT_DIALOG_SIZE = (995, 583)

    def __init__(self) -> None:
        self._titlebar_template = self._decode_template(_TITLEBAR_TEMPLATE_B64)
        self._ur_row_template = self._decode_template(_UR_ROW_TEMPLATE_B64)
        self._ok_template = self._decode_template(_OK_TEMPLATE_B64)

    @staticmethod
    def _decode_template(payload: str) -> np.ndarray:
        raw = base64.b64decode(payload)
        encoded = np.frombuffer(raw, dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError("Unable to decode embedded hardware dialog template")
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def resolve(self, image: np.ndarray) -> HardwareDialogLayout | None:
        if image is None or image.size == 0:
            return None

        dialog = self._resolve_from_titlebar(image)
        if dialog is None:
            return None

        ur_point, ur_conf = self._find_template_in_region(
            image,
            self._ur_row_template,
            dialog.tree_region,
            min_confidence=0.62,
        )
        if ur_point is None:
            print(f"[HARDWARE] UR ACTIVPILOT row not found inside tree region {dialog.tree_region}")
            return None

        ok_point, ok_conf = self._find_template_in_region(
            image,
            self._ok_template,
            (
                dialog.x + int(dialog.width * 0.78),
                dialog.y + int(dialog.height * 0.62),
                int(dialog.width * 0.20),
                int(dialog.height * 0.18),
            ),
            min_confidence=0.62,
        )
        if ok_point is None:
            print(f"[HARDWARE] OK button not found inside dialog ({dialog.x},{dialog.y},{dialog.width}x{dialog.height})")
            return None

        print(
            f"[HARDWARE] semantic targets UR ACTIVPILOT={ur_point} conf={ur_conf:.3f} "
            f"OK={ok_point} conf={ok_conf:.3f}"
        )

        return HardwareDialogLayout(
            x=dialog.x,
            y=dialog.y,
            width=dialog.width,
            height=dialog.height,
            ur_activation_point=ur_point,
            ok_button_point=ok_point,
        )

    def _resolve_from_titlebar(self, image: np.ndarray) -> HardwareDialogLayout | None:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        best: tuple[float, int, int, float] | None = None

        for scale in self._TITLE_SCALES:
            template = self._resize_template(self._titlebar_template, scale)
            if template.shape[0] >= gray.shape[0] or template.shape[1] >= gray.shape[1]:
                continue
            result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            _, confidence, _, location = cv2.minMaxLoc(result)
            if best is None or confidence > best[0]:
                best = (confidence, location[0], location[1], scale)

        if best is None:
            return None

        confidence, title_x, title_y, scale = best
        print(f"[HARDWARE] title anchor confidence={confidence:.3f} scale={scale:.2f} at=({title_x},{title_y})")
        if confidence < 0.72:
            return None

        width = int(round(self._DEFAULT_DIALOG_SIZE[0] * scale))
        height = int(round(self._DEFAULT_DIALOG_SIZE[1] * scale))
        x = int(round(title_x))
        y = int(round(title_y - 2 * scale))

        if x < 0 or y < 0 or x + width > image.shape[1] or y + height > image.shape[0]:
            return None

        print(f"[HARDWARE] dialog anchored from title=({x},{y},{width}x{height})")
        return HardwareDialogLayout(x, y, width, height, (0, 0), (0, 0))

    @staticmethod
    def _resize_template(template: np.ndarray, scale: float) -> np.ndarray:
        width = max(1, int(round(template.shape[1] * scale)))
        height = max(1, int(round(template.shape[0] * scale)))
        interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
        return cv2.resize(template, (width, height), interpolation=interpolation)

    def _find_template_in_region(
        self,
        image: np.ndarray,
        template: np.ndarray,
        region: tuple[int, int, int, int],
        *,
        min_confidence: float,
    ) -> tuple[tuple[int, int] | None, float]:
        x, y, width, height = region
        x = max(0, x)
        y = max(0, y)
        right = min(image.shape[1], x + width)
        bottom = min(image.shape[0], y + height)
        if right <= x or bottom <= y:
            return None, 0.0

        crop = cv2.cvtColor(image[y:bottom, x:right], cv2.COLOR_BGR2GRAY)
        best: tuple[float, int, int, int, int] | None = None

        for scale in self._TITLE_SCALES:
            candidate = self._resize_template(template, scale)
            if candidate.shape[0] >= crop.shape[0] or candidate.shape[1] >= crop.shape[1]:
                continue
            result = cv2.matchTemplate(crop, candidate, cv2.TM_CCOEFF_NORMED)
            _, confidence, _, location = cv2.minMaxLoc(result)
            item = (confidence, location[0], location[1], candidate.shape[1], candidate.shape[0])
            if best is None or confidence > best[0]:
                best = item

        if best is None or best[0] < min_confidence:
            return None, 0.0

        confidence, local_x, local_y, width, height = best
        center = (x + local_x + width // 2, y + local_y + height // 2)
        return center, confidence
