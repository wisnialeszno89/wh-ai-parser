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
        """Center of the first selectable ``UR ACTIVPILOT`` child row."""
        return (
            self.x + int(self.width * 0.10),
            self.y + int(self.height * 0.18),
        )

    @property
    def ok_point(self) -> tuple[int, int]:
        """Center of the lower-right OK button."""
        return (
            self.x + int(self.width * 0.912),
            self.y + int(self.height * 0.727),
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

        result = self._detect_by_modal_edges(image)
        if result is not None:
            print(
                f"[HARDWARE] modal edges bounds="
                f"({result.x},{result.y},{result.width}x{result.height})"
            )
            return result

        return self._detect_by_contour_fallback(image)

    def _detect_by_modal_edges(
        self,
        image: np.ndarray,
    ) -> HardwareDialogLayout | None:
        """Detect the centered modal from its long outer border lines."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        height, width = gray.shape

        vertical_counts = (edges > 0).sum(axis=0)
        min_count = int(height * 0.55)
        candidate_x = [
            x
            for x, count in enumerate(vertical_counts)
            if 80 <= x <= width - 1 and count >= min_count
        ]

        if len(candidate_x) < 2:
            return None

        groups: list[list[int]] = []
        for x in candidate_x:
            if not groups or x > groups[-1][-1] + 2:
                groups.append([x])
            else:
                groups[-1].append(x)

        vertical_lines = [int(round(sum(group) / len(group))) for group in groups]
        if len(vertical_lines) < 2:
            return None

        best_pair: tuple[float, int, int] | None = None
        image_center = width / 2.0

        for index, left in enumerate(vertical_lines):
            for right in vertical_lines[index + 1 :]:
                modal_width = right - left
                if modal_width < int(width * 0.55):
                    continue
                if modal_width > int(width * 0.85):
                    continue

                center = (left + right) / 2.0
                center_penalty = abs(center - image_center) / width
                width_penalty = abs((modal_width / width) - 0.675)
                line_strength = (
                    float(vertical_counts[left])
                    + float(vertical_counts[right])
                ) / (2.0 * height)

                score = (
                    line_strength * 2.0
                    - center_penalty * 1.0
                    - width_penalty * 1.5
                )

                if best_pair is None or score > best_pair[0]:
                    best_pair = (score, left, right)

        if best_pair is None:
            return None

        _, left, right = best_pair
        horizontal_counts = (edges[:, left:right + 1] > 0).sum(axis=1)
        horizontal_min = int((right - left + 1) * 0.80)

        top_candidates = [
            y
            for y, count in enumerate(horizontal_counts)
            if 80 <= y <= min(height - 1, 180)
            and count >= horizontal_min
        ]
        bottom_candidates = [
            y
            for y, count in enumerate(horizontal_counts)
            if max(350, height - 220) <= y <= height - 1
            and count >= horizontal_min
        ]

        if not top_candidates or not bottom_candidates:
            return None

        top = int(round(float(np.median(top_candidates[: min(4, len(top_candidates))]))))
        bottom = int(max(bottom_candidates))
        modal_height = bottom - top
        modal_width = right - left

        if modal_height < int(height * 0.65):
            return None

        return HardwareDialogLayout(
            x=int(left),
            y=int(top),
            width=int(modal_width),
            height=int(modal_height),
        )

    def _detect_by_contour_fallback(
        self,
        image: np.ndarray,
    ) -> HardwareDialogLayout | None:
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
            x, y, box_width, box_height = cv2.boundingRect(contour)
            area = box_width * box_height
            aspect = box_width / float(box_height) if box_height else 0.0

            if box_width < 700 or box_height < 450:
                continue
            if area < image_area * 0.25:
                continue
            if not 1.35 <= aspect <= 2.10:
                continue

            center_x = x + box_width / 2.0
            center_y = y + box_height / 2.0
            image_center_x = image_w / 2.0
            image_center_y = image_h / 2.0
            center_penalty = (
                abs(center_x - image_center_x) / image_w
                + abs(center_y - image_center_y) / image_h
            )

            score = (area / image_area) - center_penalty * 0.20
            candidates.append((score, x, y, box_width, box_height))

        if not candidates:
            return None

        _, x, y, box_width, box_height = max(
            candidates,
            key=lambda item: item[0],
        )
        return HardwareDialogLayout(x, y, box_width, box_height)
