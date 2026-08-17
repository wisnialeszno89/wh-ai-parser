from __future__ import annotations

import base64
from dataclasses import dataclass

import cv2
import numpy as np


# Real WindowHub UI crops captured from the hardware-selection dialog.
# They are intentionally wider than a text-only glyph crop so matching also
# uses the surrounding UI chrome and is less likely to match background text.
_TITLEBAR_TEMPLATE_B64 = """REPLACE_TITLEBAR"""
_UR_ROW_TEMPLATE_B64 = """REPLACE_UR_ROW"""
_OK_TEMPLATE_B64 = """REPLACE_OK"""


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
    """Resolve the real WindowHub hardware-selection modal semantically.

    MVP strategy:
      1. locate the distinctive dialog title bar,
      2. derive the modal bounds from that anchor,
      3. locate the actual ``UR ACTIVPILOT`` row inside the tree,
      4. locate the actual ``OK`` button inside the modal.

    This deliberately avoids fixed click coordinates and ignores the optional
    ``Dobór specjalny`` path.
    """

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
            print(
                f"[HARDWARE] UR ACTIVPILOT row not found "
                f"inside tree region {dialog.tree_region}"
            )
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
            print(
                f"[HARDWARE] OK button not found inside dialog "
                f"({dialog.x},{dialog.y},{dialog.width}x{dialog.height})"
            )
            return None

        print(
            f"[HARDWARE] semantic targets "
            f"UR ACTIVPILOT={ur_point} conf={ur_conf:.3f} "
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

    def _resolve_from_titlebar(
        self,
        image: np.ndarray,
    ) -> HardwareDialogLayout | None:
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
        print(
            f"[HARDWARE] title anchor confidence={confidence:.3f} "
            f"scale={scale:.2f} at=({title_x},{title_y})"
        )

        # A low-confidence title match is not safe enough for a live click.
        if confidence < 0.72:
            return None

        width = int(round(self._DEFAULT_DIALOG_SIZE[0] * scale))
        height = int(round(self._DEFAULT_DIALOG_SIZE[1] * scale))

        # The embedded crop starts at the dialog's left edge and a few pixels
        # below its outer border.
        x = int(round(title_x))
        y = int(round(title_y - 2 * scale))

        if x < 0 or y < 0:
            return None
        if x + width > image.shape[1] or y + height > image.shape[0]:
            return None

        print(
            f"[HARDWARE] dialog anchored from title="
            f"({x},{y},{width}x{height})"
        )
        return HardwareDialogLayout(
            x=x,
            y=y,
            width=width,
            height=height,
            ur_activation_point=(0, 0),
            ok_button_point=(0, 0),
        )

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
            if (
                candidate.shape[0] >= crop.shape[0]
                or candidate.shape[1] >= crop.shape[1]
            ):
                continue

            result = cv2.matchTemplate(crop, candidate, cv2.TM_CCOEFF_NORMED)
            _, confidence, _, location = cv2.minMaxLoc(result)
            item = (
                confidence,
                location[0],
                location[1],
                candidate.shape[1],
                candidate.shape[0],
            )
            if best is None or confidence > best[0]:
                best = item

        if best is None or best[0] < min_confidence:
            return None, 0.0

        confidence, local_x, local_y, width, height = best
        center = (
            x + local_x + width // 2,
            y + local_y + height // 2,
        )
        return center, confidence
