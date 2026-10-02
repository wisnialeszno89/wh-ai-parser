from __future__ import annotations

from dataclasses import dataclass

from app.runtime.execution.vision.models.control_type import ControlType
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)


@dataclass(frozen=True, slots=True)
class VerificationResult:
    verified: bool
    reason: str
    iou: float = 0.0


class ExecutionVerifier:
    """
    Verifies that a tracked visual target still matches
    the state that was previously observed.

    This component performs no interaction and never touches hardware.
    """

    def __init__(
        self,
        *,
        min_confidence: float = 0.0,
        min_consecutive_observations: int = 2,
        min_iou: float = 0.70,
    ) -> None:
        self.min_confidence = min_confidence
        self.min_consecutive_observations = min_consecutive_observations
        self.min_iou = min_iou

    def verify(
        self,
        *,
        tracked_object: TrackedObject,
        expected_control_type: ControlType,
        expected_bounds: Rect,
    ) -> VerificationResult:
        if tracked_object.status is TrackedObjectStatus.LOST:
            return VerificationResult(
                verified=False,
                reason="Tracked object is lost",
            )

        if tracked_object.control_type != expected_control_type:
            return VerificationResult(
                verified=False,
                reason="Control type changed",
            )

        if tracked_object.confidence < self.min_confidence:
            return VerificationResult(
                verified=False,
                reason="Confidence below verification threshold",
            )

        if (
            tracked_object.consecutive_observations
            < self.min_consecutive_observations
        ):
            return VerificationResult(
                verified=False,
                reason="Insufficient consecutive observations",
            )

        current_bounds = tracked_object.object.bounds
        iou = self._iou(expected_bounds, current_bounds)

        if iou < self.min_iou:
            return VerificationResult(
                verified=False,
                reason="Target geometry changed",
                iou=iou,
            )

        return VerificationResult(
            verified=True,
            reason="Target verified",
            iou=iou,
        )

    @staticmethod
    def _iou(first: Rect, second: Rect) -> float:
        left = max(first.left, second.left)
        top = max(first.top, second.top)
        right = min(first.right, second.right)
        bottom = min(first.bottom, second.bottom)

        intersection_width = max(0, right - left)
        intersection_height = max(0, bottom - top)
        intersection_area = (
            intersection_width * intersection_height
        )

        if intersection_area == 0:
            return 0.0

        union_area = first.area + second.area - intersection_area

        if union_area <= 0:
            return 0.0

        return intersection_area / union_area
