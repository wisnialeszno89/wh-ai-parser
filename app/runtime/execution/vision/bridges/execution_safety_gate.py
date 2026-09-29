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
    Prevents interaction execution when the current evidence does not
    support the requested action.

    When an explicit interaction capability is supplied by the
    Universal Agent Core, it is the authoritative semantic capability
    signal for this gate. The gate still requires a live, stable tracked
    object and positive capability confidence.

    Lower-level callers that do not provide interaction capability retain
    the legacy BUTTON-only safety contract.
    """

    def can_execute(
        self,
        tracked_object: TrackedObject,
        action: InteractionAction,
        *,
        interaction_capability=None,
        interaction_capability_confidence: float | None = None,
    ) -> bool:

        if tracked_object.status is TrackedObjectStatus.LOST:
            return False

        if tracked_object.confidence <= 0.0:
            return False

        if tracked_object.consecutive_observations < 2:
            return False

        if interaction_capability is not None:
            capability = getattr(
                interaction_capability,
                "value",
                interaction_capability,
            )

            if not isinstance(capability, str):
                return False

            if capability.strip().casefold() != "clickable":
                return False

            try:
                capability_confidence = float(
                    interaction_capability_confidence
                )
            except (TypeError, ValueError):
                return False

            if capability_confidence <= 0.0:
                return False
        elif tracked_object.control_type != ControlType.BUTTON:
            return False

        if action is InteractionAction.CLICK:
            return True

        return False
