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
    right(self) -> int:
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
        """Center of the first visible hardware-family row.

        MVP intentionally selects the first visible hardware family, currently
        the ``UR ACTIVPILOT`` entry shown in the observed WindowHub dialog.
        """
        return (
            self.x + int(self.width * 0.16),
            self.y + int(self.height * 0.14),
        )

    @property
    def ok_point(self) -> tuple[int, int]:
        """Center point of the lower-right OK button."""
        return (
            self.x + int(self.width * 0.91),
            self.y + int(self.height * 0.71),
        )

    @property
    def cancel_region(self) -> tuple[int, int, int, int]:
        return (
            self.x + int(self.width * 0.86),
            self.y + int(self.height * 0.75),
            int(self.width * 0.10),
            int(self.height * 0.10),
        )


class HardwareDialogResolver:
    """Detect the hardware-selection modal and expose safe MVP targets.

    MVP flow:
      1. detect the dialog,
      2. click the first visible hardware family (currently UR ACTIVPILOT),
      3. click OK.

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

            center_x = x + width / 2.0
            image_center_x = image.shape[1] / 2.0
            center_penalty = abs(center_x - image_center_x) / image.shape[1]
            score = area / image_area - center_penalty * 0.15
            candidates.append((score, x, y, width, height))

        if not candidates:
            return None

        _, x, y, width, height = max(
            candidates,
            key=lambda item: item[0],
        )
        return HardwareDialogLayout(x, y, width, height)
