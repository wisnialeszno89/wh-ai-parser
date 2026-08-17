from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


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
    def ok_region(self) -> tuple[int, int, int, int]:
        return (
            self.x + int(self.width * 0.76),
            self.y + int(self.height * 0.60),
            int(self.width * 0.23),
            int(self.height * 0.24),
        )

    @property
    def first_tree_item_point(self) -> tuple[int, int]:
        return self.ur_activation_point

    @property
    def ok_point(self) -> tuple[int, int]:
        return self.ok_button_point


class HardwareDialogResolver:
    """Resolve the WindowHub hardware-selection dialog structurally.

    MVP flow:
      1. detect the centered modal from its outer rectangle,
      2. locate the first selectable child row in the left tree,
      3. locate the lower-right OK button, with a geometry fallback bounded to
         the detected modal.

    The geometry is relative to the observed dialog, not to the desktop, so
    moving or resizing the WindowHub window does not change the click targets.
    """

    def resolve(self, image: np.ndarray) -> HardwareDialogLayout | None:
        if image is None or image.size == 0:
            return None

        dialog = self._detect_dialog(image)
        if dialog is None:
            print("[HARDWARE] structural dialog detection failed")
            return None

        ur_point = self._find_first_selectable_tree_row(image, dialog)
        if ur_point is None:
            print(
                f"[HARDWARE] selectable tree row not found in {dialog.tree_region}"
            )
            return None

        ok_point = self._find_ok_button(image, dialog)
        if ok_point is None:
            print("[HARDWARE] OK geometry fallback unavailable")
            return None

        print(
            f"[HARDWARE] structural targets "
            f"UR ACTIVPILOT={ur_point} OK={ok_point}"
        )

        return HardwareDialogLayout(
            x=dialog.x,
            y=dialog.y,
            width=dialog.width,
            height=dialog.height,
            ur_activation_point=ur_point,
            ok_button_point=ok_point,
        )

    def _detect_dialog(self, image: np.ndarray) -> HardwareDialogLayout | None:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        height, width = gray.shape[:2]

        vertical = (edges > 0).sum(axis=0)
        horizontal = (edges > 0).sum(axis=1)

        vertical_candidates = [
            x
            for x, value in enumerate(vertical)
            if 100 <= x <= width - 100 and value >= int(height * 0.45)
        ]
        horizontal_candidates = [
            y
            for y, value in enumerate(horizontal)
            if 50 <= y <= height - 50 and value >= int(width * 0.45)
        ]

        vertical_groups = self._group_positions(vertical_candidates, gap=3)
        horizontal_groups = self._group_positions(horizontal_candidates, gap=3)

        vertical_lines = [int(round(np.mean(group))) for group in vertical_groups]
        horizontal_lines = [int(round(np.mean(group))) for group in horizontal_groups]

        if len(vertical_lines) < 2 or len(horizontal_lines) < 2:
            return None

        best: tuple[float, int, int, int, int] | None = None
        image_center = (width / 2.0, height / 2.0)

        for left in vertical_lines:
            for right in vertical_lines:
                if right <= left:
                    continue
                box_width = right - left
                if not 750 <= box_width <= 1150:
                    continue

                for top in horizontal_lines:
                    for bottom in horizontal_lines:
                        if bottom <= top:
                            continue
                        box_height = bottom - top
                        if not 480 <= box_height <= 700:
                            continue

                        center = ((left + right) / 2.0, (top + bottom) / 2.0)
                        center_penalty = (
                            abs(center[0] - image_center[0]) / width
                            + abs(center[1] - image_center[1]) / height
                        )

                        expected_width = 995.0
                        expected_height = 583.0
                        shape_penalty = (
                            abs(box_width - expected_width) / expected_width
                            + abs(box_height - expected_height) / expected_height
                        )

                        strength = (
                            float(vertical[left])
                            + float(vertical[right])
                            + float(horizontal[top])
                            + float(horizontal[bottom])
                        ) / (2.0 * (width + height))

                        score = strength * 2.0 - center_penalty - shape_penalty
                        candidate = (score, left, top, box_width, box_height)
                        if best is None or candidate[0] > best[0]:
                            best = candidate

        if best is None:
            return None

        _, x, y, box_width, box_height = best
        print(
            f"[HARDWARE] structural dialog bounds="
            f"({x},{y},{box_width}x{box_height})"
        )

        return HardwareDialogLayout(
            x=x,
            y=y,
            width=box_width,
            height=box_height,
            ur_activation_point=(0, 0),
            ok_button_point=(0, 0),
        )

    @staticmethod
    def _group_positions(values: list[int], gap: int) -> list[list[int]]:
        groups: list[list[int]] = []
        for value in values:
            if not groups or value - groups[-1][-1] > gap:
                groups.append([value])
            else:
                groups[-1].append(value)
        return groups

    def _find_first_selectable_tree_row(
        self,
        image: np.ndarray,
        dialog: HardwareDialogLayout,
    ) -> tuple[int, int] | None:
        x, y, width, height = dialog.tree_region
        x2 = min(image.shape[1], x + width)
        y2 = min(image.shape[0], y + height)
        crop = image[max(0, y):y2, max(0, x):x2]
        if crop.size == 0:
            return None

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        dark = cv2.inRange(gray, 0, 150)
        projection = (dark > 0).sum(axis=1)

        row_candidates = [
            index
            for index, value in enumerate(projection)
            if value >= max(6, int(crop.shape[1] * 0.015))
        ]
        groups = self._group_positions(row_candidates, gap=4)
        row_centers = [int(round(np.mean(group))) for group in groups]
        row_centers = [row for row in row_centers if 8 <= row <= crop.shape[0] - 8]

        if not row_centers:
            return None

        # In the real dialog the first general family row (N ACTIVPILOT...) is
        # immediately followed by the first selectable child (UR ACTIVPILOT).
        # Prefer a row near 14-16% of the dialog height and away from the tree
        # expander gutter.
        expected_local_y = int(crop.shape[0] * 0.15)
        target_y = min(
            row_centers,
            key=lambda row: abs(row - expected_local_y),
        )
        target_x = int(crop.shape[1] * 0.34)
        point = (x + target_x, y + target_y)
        print(f"[HARDWARE] tree row candidate={point} local_y={target_y}")
        return point

    def _find_ok_button(
        self,
        image: np.ndarray,
        dialog: HardwareDialogLayout,
    ) -> tuple[int, int] | None:
        x, y, width, height = dialog.ok_region
        x2 = min(image.shape[1], x + width)
        y2 = min(image.shape[0], y + height)
        crop = image[max(0, y):y2, max(0, x):x2]

        if crop.size:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 40, 130)
            contours, _ = cv2.findContours(
                edges,
                cv2.RETR_LIST,
                cv2.CHAIN_APPROX_SIMPLE,
            )

            candidates: list[tuple[float, tuple[int, int, int, int]]] = []
            for contour in contours:
                bx, by, bw, bh = cv2.boundingRect(contour)
                if not 50 <= bw <= 190 or not 16 <= bh <= 65:
                    continue
                aspect = bw / float(bh)
                if not 1.8 <= aspect <= 7.5:
                    continue
                center_y = by + bh * 0.5
                candidates.append((center_y, (bx, by, bw, bh)))

            if candidates:
                _, (bx, by, bw, bh) = max(candidates, key=lambda item: item[0])
                point = (x + bx + bw // 2, y + by + bh // 2)
                print(f"[HARDWARE] OK button candidate={point}")
                return point

        # Geometry fallback is constrained to the observed dialog. This is
        # intentionally not a desktop coordinate and works when the button
        # border is faint or anti-aliased.
        point = (
            dialog.x + int(dialog.width * 0.912),
            dialog.y + int(dialog.height * 0.727),
        )
        print(f"[HARDWARE] OK geometry fallback={point}")
        return point
