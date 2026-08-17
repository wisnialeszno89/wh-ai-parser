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
        """Center of the first selectable UR ACTIVPILOT child row."""
        return (
            self.x + int(self.width * 0.10),
            self.y + int(self.height * 0.17),
        )

    @property
    def ok_point(self) -> tuple[int, int]:
        """Center of the lower-right OK button."""
        return (
            self.x + int(self.width * 0.91),
            self.y + int(self.height * 0.72),
        )

    @property
    def cancel_region(self) -> tuple[int, int, int, int]:
        return (
            self.x + int(self.width * 0.86),
            self.y + int(self.height * 0.78),
            int(self.width * 0.10),
            int(self.height * 0.10),
        )


class HardwareDialogResolver:
    """Detect and drive the MVP hardware-selection modal.

    MVP flow:
      1. detect the actual centered hardware dialog,
      2. click the first visible UR ACTIVPILOT child row,
      3. re-observe the dialog,
      4. click OK.

    The optional 'Dobór specjalny' path and semantic hardware preferences are
    intentionally out of scope for this first working implementation.
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

        image_h, image_w = image.shape[:2]
        image_area = image_h * image_w
        candidates: list[tuple[float, int, int, int, int]] = []

        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)
            area = width * height
            aspect = width / float(height) if height else 0.0

            # WindowHub's hardware dialog is a large, wide modal. The stronger
            # geometry filter prevents the document table/canvas from being
            # mistaken for the dialog.
            if width < 700 or height < 450:
                continue
            if area < image_area * 0.25:
                continue
            if not 1.35 <= aspect <= 2.10:
                continue

            center_x = x + width / 2.0
            center_y = y + height / 2.0
            image_center_x = image_w / 2.0
            image_center_y = image_h / 2.0
            center_penalty = (
                abs(center_x - image_center_x) / image_w
                + abs(center_y - image_center_y) / image_h
            )

            score = (area / image_area) - center_penalty * 0.20
            candidates.append((score, x, y, width, height))

        if not candidates:
            return None

        _, x, y, width, height = max(
            candidates,
            key=lambda item: item[0],
        )
        return HardwareDialogLayout(x, y, width, height)
