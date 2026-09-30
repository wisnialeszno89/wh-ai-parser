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


    def can_execute_uia_element(
        self,
        *,
        metadata,
        interaction_capability=None,
        interaction_capability_confidence: float | None = None,
        window_handle=None,
        require_foreground: bool = False,
    ) -> bool:
        """
        Validate a UI Automation target that does not have a visual
        tracked-object identity.

        UIA-only execution is intentionally narrower than the normal
        tracked-object path: it requires WindowHub UIA provenance,
        an enabled/visible interactive control, positive clickable
        capability confidence, and (for LIVE execution) a matching
        foreground window handle.
        """

        if not isinstance(metadata, dict):
            return False

        if metadata.get("source") != "windowhub_ui_automation":
            return False

        if metadata.get("uia_enabled") is not True:
            return False

        if metadata.get("uia_visible") is not True:
            return False

        control_type = metadata.get("uia_control_type")
        if not isinstance(control_type, str):
            return False

        allowed_control_types = {
            "button",
            "checkbox",
            "combobox",
            "hyperlink",
            "listitem",
            "menuitem",
            "radiobutton",
            "splitbutton",
            "tabitem",
            "treeitem",
        }

        if control_type.strip().casefold() not in allowed_control_types:
            return False

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

        if not require_foreground:
            return True

        try:
            handle = int(window_handle)
        except (TypeError, ValueError):
            return False

        if handle <= 0:
            return False

        if __import__("os").name != "nt":
            return False

        import ctypes

        try:
            foreground = int(
                ctypes.windll.user32.GetForegroundWindow()
            )
        except Exception:
            return False

        return foreground == handle
