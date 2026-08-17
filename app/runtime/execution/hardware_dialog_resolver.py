from __future__ import annotations

import base64
from dataclasses import dataclass

import cv2
import numpy as np


# Exact crop of the stable dialog title "Wybór okuć: 1" from the real
# WindowHub UI. We use it only to anchor the modal; targets are calculated
# relative to the detected modal afterwards.
_TITLE_TEMPLATE_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAFwAAAAbCAIAAAB+0H/bAAAFAElEQVR4nNVYX2haVxj/bgk1gVy87/mjpi/JRrIEE6IxtJvGkId0YEwyaFnImrA9JdHJGAv5Q7qyjRartg+jnQZZ2SBGky0Po/RGWYZeLW1Z1zK6l9bbPQ4Gdg5a83L3cMzN9er9G2fbH6LnO/ec833nd7/v8zsH29vb29/fh1qBYRiuSJKk3W6vmXaZwP76+5/jxzUv24yjo8g1xpM5wPgd5UOKqHttGamwpbJtC07AhBkBgGOqDHrpENsSgihBEtPrDheQVvSqgxEOH3En4qHucPjrQY2EfYiX0khRjLLwwVQtUyPIemNSg6QXOXJOqR2JKnyYKUuoshapU65JhZbaodILUmxi3au2q0qQa2KVXJaR7SmYWqcQKackoGyC/NpMUulhTnE6RmPRCCv2dHWwIk1niUZNxRdB4IK1XyadEnkqglg04nHPyR/f0/XGFsdyHtJpSos30HRWxkpFHo8VMyUGZ85OUakk6qXpbDb7hBXv3b0zM/uRfCsRLl38MpcvqHphsmoz9An4vV9f+8Y5PlE6q9ju7nrz0sWvlCo9DB9jb9+F86uojVhIxEkkUqnkwOCgvKWLoOms13e1TF11wHXZ/n6z2Ww+kPia7j/4HQC0eIPUkiUTD8NHbzAAAHKz77/7dmLyPVZMxEmjsc/jmve459Fgms72dHWgdiwaIXANgWsCfi/7tLuzvbuzndvZ09UR8HsJXJNJp7gWOB2jaDq7IItYNELg9Zk05XHPs7HMbY85To8MW7V4g99/ORbdHHO8K7V5aUaAV6dYbfZ7d+8AQHyXNJktSES86A2GuQU36zs//rC1tLKG2lQqmcsXcvnC6vIi2nB3Z/vNWwnUGV4Psnv48+nTXL5gMltYjR73vF7fhkZOn5t1OkZZEzNpauaDqVz+hck8UHErY47TJ0+9/Sz//Fn+ucv1sSo6KjACvDplYHCQSiabmppsQ3YAGLAMUqkkYGC12REvbSdOZNIpk9kSXg/++uARmuX1XUGNtc+/uH07AwC2ITu786WVNSqVdI5PAsDcgptnUCJObu/8hIQFl2d1eRG1aTo7MmzN5V9wDyG8RB/fJbe2d1jROT7hHJ9QwAaAUGCXkOIcn5yZfr9Vpztzdgo4WYZNKJ98+tnmxgZAkaZyNDe3lHe26nRSlhWPLAZDG+p68vgxAGTSlFnATaoBwVTHL/NtQ/bwetDY2wdYMcuEgteMxj701GS2JOLkZmQDZRyEWDQCGNB0dnV50djbZxqwxHdJNnFcOL/a328SUm+1DV0N+JCJAb/Xahti+397+Ghk2IqCt1WnSx38FYaC11lT/f7LHDMkcwpT+hEEn5STp96Bg6QLAFab3WBoY0UAmD43m4iT3LxApZJEo6a7sz0UvoFG3n/4x8iwFaXPpZU17uBSE8Hru0LTWQKvJ/D6X/Z+ZiMRAPR6w81bibc6O/x+r8vlCQWva/F6LV4/M/shADDAxLZ3wushLd6AEq0oHaDoLxDL/VuQPxoAAj5vc0sLyhFHsEHssXC1zvAE2XW9wuJYKSlEo0bWFDEzlDJyxDpH8dFJ8OqgPPICPi/RqAmFb6i1TDqYq8SI3NwhpFrQU9jFVB49+Z4uaw7G16aOETXgKhY8JVfv5ohRe9FZO0ZKl5B/daBaBe8OGMQsZyo4ixJdysFVxhx8/T+kMAc/FTco6jgMMKDGTxUxggZjFRkBgP8AnmrplfqzVYcAAAAASUVORK5CYII="
)


@dataclass(frozen=True, slots=True)
class HardwareDialogLayout:
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
        # The first selectable child row is UR ACTIVPILOT. Keep the click
        # well inside the left tree, away from the row expand/collapse gutter.
        return (
            self.x + int(self.width * 0.15),
            self.y + int(self.height * 0.175),
        )

    @property
    def ok_point(self) -> tuple[int, int]:
        return (
            self.x + int(self.width * 0.91),
            self.y + int(self.height * 0.725),
        )

    @property
    def cancel_region(self) -> tuple[int, int, int, int]:
        return (
            self.x + int(self.width * 0.86),
            self.y + int(self.height * 0.79),
            int(self.width * 0.10),
            int(self.height * 0.10),
        )


class HardwareDialogResolver:
    """Resolve the real WindowHub hardware-selection modal.

    Primary strategy: anchor from the dialog title text. This prevents the
    document grid/table behind the modal from being mistaken for the dialog.
    Geometry/contour detection remains only as a fallback.
    """

    _TITLE_ORIGIN_OFFSET = (-6, -2)
    _DEFAULT_DIALOG_SIZE = (995, 583)
    _TITLE_SCALES = (0.85, 0.90, 0.95, 1.0, 1.05, 1.10, 1.15)

    def __init__(self) -> None:
        raw = base64.b64decode(_TITLE_TEMPLATE_B64)
        encoded = np.frombuffer(raw, dtype=np.uint8)
        template = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
        if template is None:
            raise RuntimeError("Unable to decode embedded hardware dialog title template")
        self._title_template = template

    def resolve(self, image: np.ndarray) -> HardwareDialogLayout | None:
        if image is None or image.size == 0:
            return None

        anchored = self._resolve_from_title(image)
        if anchored is not None:
            return anchored

        return self._resolve_from_geometry(image)

    def _resolve_from_title(self, image: np.ndarray) -> HardwareDialogLayout | None:
        best: tuple[float, int, int, float, int, int] | None = None
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(self._title_template, cv2.COLOR_BGR2GRAY)

        for scale in self._TITLE_SCALES:
            width = max(1, int(round(template_gray.shape[1] * scale)))
            height = max(1, int(round(template_gray.shape[0] * scale)))
            if width >= gray_image.shape[1] or height >= gray_image.shape[0]:
                continue

            resized = cv2.resize(
                template_gray,
                (width, height),
                interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC,
            )
            result = cv2.matchTemplate(gray_image, resized, cv2.TM_CCOEFF_NORMED)
            _, confidence, _, location = cv2.minMaxLoc(result)

            if best is None or confidence > best[0]:
                best = (confidence, location[0], location[1], scale, width, height)

        if best is None:
            return None

        confidence, match_x, match_y, scale, _, _ = best
        print(
            f"[HARDWARE] title anchor confidence={confidence:.3f} "
            f"scale={scale:.2f} at=({match_x},{match_y})"
        )

        if confidence < 0.68:
            return None

        x = int(round(match_x + self._TITLE_ORIGIN_OFFSET[0] * scale))
        y = int(round(match_y + self._TITLE_ORIGIN_OFFSET[1] * scale))
        width, height = self._DEFAULT_DIALOG_SIZE

        # Adjust the default size proportionally when the title itself scales.
        width = int(round(width * scale))
        height = int(round(height * scale))

        if x < 0 or y < 0 or width < 700 or height < 450:
            return None
        if x + width > image.shape[1] or y + height > image.shape[0]:
            return None

        return HardwareDialogLayout(x, y, width, height)

    def _resolve_from_geometry(self, image: np.ndarray) -> HardwareDialogLayout | None:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 60, 140)
        image_h, image_w = image.shape[:2]
        image_area = image_h * image_w
        candidates: list[tuple[float, int, int, int, int]] = []

        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        for contour in contours:
            x, y, width, height = cv2.boundingRect(contour)
            area = width * height
            aspect = width / float(height) if height else 0.0
            if width < 700 or height < 450:
                continue
            if area < image_area * 0.25:
                continue
            if not 1.35 <= aspect <= 2.10:
                continue

            center_x = x + width / 2.0
            center_y = y + height / 2.0
            penalty = (
                abs(center_x - image_w / 2.0) / image_w
                + abs(center_y - image_h / 2.0) / image_h
            )
            candidates.append(
                (area / image_area - penalty * 0.20, x, y, width, height)
            )

        if not candidates:
            return None

        _, x, y, width, height = max(candidates, key=lambda item: item[0])
        print(
            f"[HARDWARE] geometry dialog candidate="
            f"({x},{y},{width}x{height})"
        )
        return HardwareDialogLayout(x, y, width, height)
