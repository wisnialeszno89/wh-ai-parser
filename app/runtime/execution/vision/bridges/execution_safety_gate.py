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
        expected_foreground_handle=None,
        observed_window_handles=(),
    ) -> bool:
        """Activate only a current inventory window while the observed foreground is unchanged."""
        if (
            isinstance(window_handle, bool)
            or isinstance(expected_foreground_handle, bool)
        ):
            return False
        try:
            handle = int(window_handle)
            expected_foreground = int(expected_foreground_handle)
        except (TypeError, ValueError, OverflowError):
            return False
        if (
            handle <= 0
            or expected_foreground <= 0
            or handle == expected_foreground
            or __import__("os").name != "nt"
        ):
            return False

        if isinstance(observed_window_handles, (str, bytes)):
            return False
        try:
            observed = {
                candidate
                for candidate in observed_window_handles
                if isinstance(candidate, int)
                and not isinstance(candidate, bool)
                and candidate > 0
            }
        except (TypeError, ValueError, OverflowError):
            return False
        if handle not in observed or expected_foreground not in observed:
            return False

        import ctypes
        from ctypes import wintypes

        try:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            target_hwnd = wintypes.HWND(handle)
            is_window = user32.IsWindow
            is_window.argtypes = (wintypes.HWND,)
            is_window.restype = wintypes.BOOL
            is_visible = user32.IsWindowVisible
            is_visible.argtypes = (wintypes.HWND,)
            is_visible.restype = wintypes.BOOL
            get_foreground = user32.GetForegroundWindow
            get_foreground.argtypes = ()
            get_foreground.restype = wintypes.HWND

            foreground_value = get_foreground()
            foreground = int(
                getattr(foreground_value, "value", foreground_value) or 0
            )
            return (
                foreground == expected_foreground
                and bool(is_window(target_hwnd))
                and bool(is_visible(target_hwnd))
            )
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
