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
        tracked-object path: it requires trusted Windows UIA provenance,
        an enabled/visible interactive control, positive clickable
        capability confidence, and (for LIVE execution) a matching
        foreground window handle.
        """

        if not isinstance(metadata, dict):
            return False

        source = metadata.get("source")
        if not isinstance(source, str) or source not in {
            "windowhub_ui_automation",
            "windows_ui_automation",
        }:
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
            "edit",
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


    def can_activate_window(
        self,
        *,
        window_handle=None,
        observed_window_handles=(),
    ) -> bool:
        """Only activate a still-visible HWND included in the latest local inventory."""
        try:
            handle = int(window_handle)
        except (TypeError, ValueError, OverflowError):
            return False
        if handle <= 0 or __import__("os").name != "nt":
            return False

        if isinstance(observed_window_handles, (str, bytes)):
            return False
        try:
            observed = {
                int(candidate)
                for candidate in observed_window_handles
                if not isinstance(candidate, bool)
            }
        except (TypeError, ValueError, OverflowError):
            return False
        if handle not in observed:
            return False

        import ctypes
        from ctypes import wintypes

        try:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            hwnd = wintypes.HWND(handle)
            is_window = user32.IsWindow
            is_window.argtypes = (wintypes.HWND,)
            is_window.restype = wintypes.BOOL
            is_visible = user32.IsWindowVisible
            is_visible.argtypes = (wintypes.HWND,)
            is_visible.restype = wintypes.BOOL
            return bool(is_window(hwnd) and is_visible(hwnd))
        except Exception:
            return False

    def can_execute_keyboard_input(
        self,
        *,
        window_handle=None,
        require_foreground: bool = False,
    ) -> bool:
        """Allow global keyboard input only while the observed window is foreground."""
        if not require_foreground:
            return True

        try:
            handle = int(window_handle)
        except (TypeError, ValueError, OverflowError):
            return False
        if handle <= 0 or __import__("os").name != "nt":
            return False

        import ctypes

        try:
            foreground = int(ctypes.windll.user32.GetForegroundWindow())
        except Exception:
            return False

        return foreground == handle
