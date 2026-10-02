from __future__ import annotations

from collections.abc import Iterable

from app.runtime.execution.vision.models.gui_object import GUIObject
from app.runtime.execution.vision.models.tracked_object import TrackedObject, TrackedObjectStatus


class TrackedObjectGUIBridge:
    """
    Resolves a currently visible tracked vision object to the existing
    GUIObject tree.

    Temporal identity and interaction representation remain separate:

        TrackedObject -> temporal identity
        GUIObject     -> concrete visual interaction object

    LOST tracks are never resolved because their corresponding object is
    not confirmed to be present in the current frame.
    """

    def __init__(self, min_iou: float = 0.5) -> None:
        if not 0.0 <= min_iou <= 1.0:
            raise ValueError("min_iou must be between 0.0 and 1.0")

        self.min_iou = min_iou

    def resolve(
        self,
        tracked_object: TrackedObject,
        root: GUIObject,
    ) -> GUIObject | None:
        """
        Find the existing GUIObject corresponding to a currently visible
        tracked object.

        LOST tracks are intentionally rejected.
        """

        if tracked_object.status is TrackedObjectStatus.LOST:
            return None

        tracked_bounds = tracked_object.object.bounds

        best_match: GUIObject | None = None
        best_iou = 0.0

        for candidate in self._walk(root):
            if candidate.bounds is None:
                continue

            iou = self._iou(tracked_bounds, candidate.bounds)

            if iou > best_iou:
                best_iou = iou
                best_match = candidate

        if best_match is None:
            return None

        if best_iou < self.min_iou:
            return None

        return best_match

    def _walk(self, root: GUIObject) -> Iterable[GUIObject]:
        yield root

        for child in root.children:
            yield from self._walk(child)

    @staticmethod
    def _iou(a, b) -> float:
        left = max(a.left, b.left)
        top = max(a.top, b.top)
        right = min(a.right, b.right)
        bottom = min(a.bottom, b.bottom)

        intersection_width = max(0, right - left)
        intersection_height = max(0, bottom - top)
        intersection_area = (
            intersection_width * intersection_height
        )

        if intersection_area == 0:
            return 0.0

        union_area = (
            a.area
            + b.area
            - intersection_area
        )

        if union_area <= 0:
            return 0.0

        return intersection_area / union_area

