from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True, slots=True)
class HardwareDialogLayout:
    """Observed geometry of the WindowHub hardware-selection dialog."""

    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def tree_region(self) -> tuple[int, int, int, int]:
        # Relative MVP region: left-side hardware-family tree.
        return (
            self.x + int(self.width * 0.02),
            self.y + int(self.height * 0.08),
            int(self.width * 0.48),
            int(self.height * 0.52),
        )

    @property
    def parts_region(self) -> tuple[int, int, int, int]:
        # Relative MVP region: right-side parts table.
        return (
            self.x + int(self.width * 0.52),
            self.y + int(self.height * 0.08),
            int(self.width * 0.42),
            int(self.height * 0.34),
        )

    @property
    def ok_region(self) -> tuple[int, int, int, int]:
        # Relative MVP region: lower-right OK button.
        return (
            self.x + int(self.width * 0.86),
            self.y + int(self.height * 0.78),
            int(self.width * 0.10),
            int(self.height * 0.10),
        )

    @property
    def cancel_region(self) -> tuple[int, int, int, int]:
        return (
            self.x + int(self.width * 0.86),
            self.y + int(self.height * 0.84),
            int(self.width * 0.10),
            int(self.height * 0.10),
        )


class HardwareDialogResolver:
    """Detect the hardware-selection modal before attempting any selection.

    MVP intentionally resolves geometry only. It does not choose an item and
    does not use the optional 'Dobór specjalny' path.
    """

    def resolve(self, image: np.ndarray) -> HardwareDialogLayout | None:
        if image is None or image.size == 0:
            return None

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mask = cv2.inRange(gray, 195, 255)

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        image_area = image.shape[0] * image.shape[1]
        candidates: list[tuple[float, int, int, int, int]] = []

        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)
            area = width * height

            if width < 500 or height < 300:
                continue
            if area < image_area * 0.12:
                continue
            if x <= 0 and y <= 0:
                continue

            # Prefer a large, centered modal over ordinary white application
            # areas. The dialog shown by WindowHub is a substantial centered
            # rectangle, while the document grid/canvas is much less compact.
            center_x = x + width / 2.0
            image_center_x = image.shape[1] / 2.0
            center_penalty = abs(center_x - image_center_x) / image.shape[1]
            score = area / image_area - center_penalty * 0.15
            candidates.append((score, x, y, width, height))

        if not candidates:
            return None

        _, x, y, width, height = max(candidates, key=lambda item: item[0])
        return HardwareDialogLayout(x, y, width, height)
