from __future__ import annotations

from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)
from app.runtime.execution.vision.models.control_type import (
    ControlType,
)
from app.runtime.execution.vision.models.tracked_object import (
    TrackedObject,
    TrackedObjectStatus,
)


class ExecutionSafetyGate:
    """
    Prevents interaction execution when the current vision evidence
    does not support the requested action.

    The gate intentionally operates on semantic tracking information,
    before a tracked object is converted into an executable GUI target.
    """

    def can_execute(
        self,
        tracked_object: TrackedObject,
        action: InteractionAction,
    ) -> bool:

        if tracked_object.status is TrackedObjectStatus.LOST:
            return False

        if tracked_object.control_type != ControlType.BUTTON:
            return False

        if tracked_object.confidence <= 0.0:
            return False

        if tracked_object.consecutive_observations < 2:
            return False

        if action is InteractionAction.CLICK:
            return True

        return False
