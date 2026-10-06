from __future__ import annotations

import ctypes

from app.agent.environment.windowhub_environment_adapter import (
    WindowHubEnvironmentAdapter,
)
from app.agent.learning.human_action_event import HumanActionEvent
from app.agent.learning.human_action_observer import (
    HumanActionCallback,
    HumanActionObserver,
)
from app.agent.learning.windows_mouse_observer import WindowsMouseObserver


GA_ROOT = 2
GA_ROOTOWNER = 3


class WindowHubMouseObserver(HumanActionObserver):
    """
    WindowHub-scoped mouse observer.

    The underlying Windows observer watches the left mouse button globally,
    while this adapter accepts clicks whose top-level window is WindowHub or
    whose root owner is WindowHub (for owned dialogs/modal forms). Coordinates
    are converted from screen space to WindowHub-local space before the
    semantic interpreter sees them.
    """

    def __init__(
        self,
        *,
        mouse_observer: WindowsMouseObserver | None = None,
    ) -> None:
        self._mouse_observer = (
            mouse_observer
            if mouse_observer is not None
            else WindowsMouseObserver()
        )

    def start(
        self,
        callback: HumanActionCallback,
    ) -> None:
        self._mouse_observer.start(
            self._handle_event(callback)
        )

    def stop(self) -> None:
        self._mouse_observer.stop()

    def _handle_event(
        self,
        callback: HumanActionCallback,
    ):
        def handle(event: HumanActionEvent) -> None:
            if event.x is None or event.y is None:
                return

            local = self._windowhub_local_position(
                event.x,
                event.y,
            )
            if local is None:
                return

            x, y = local

            metadata = {
                **dict(event.metadata or {}),
                "scope": "WindowHub",
            }

            # Capture a semantic hint at the exact moment of the physical
            # click. This prevents a fast second click from being interpreted
            # against a later UI state after the dialog has already changed.
            event_semantics = self._semantic_target_at_screen_position(
                event.x,
                event.y,
            )
            if event_semantics is not None:
                metadata.update(event_semantics)

            callback(
                HumanActionEvent(
                    action_type=event.action_type,
                    x=x,
                    y=y,
                    value=event.value,
                    metadata=metadata,
                )
            )

        return handle

    @staticmethod
    def _semantic_target_at_screen_position(
        screen_x: int,
        screen_y: int,
    ) -> dict[str, object] | None:
        try:
            point = ctypes.wintypes.POINT(
                int(screen_x),
                int(screen_y),
            )
            user32 = ctypes.windll.user32
            hwnd = int(user32.WindowFromPoint(point))
            if hwnd <= 0:
                return None

            from pywinauto import Desktop

            item = (
                Desktop(backend="uia")
                .window(handle=hwnd)
                .wrapper_object()
            )
            info = item.element_info

            control_type = str(
                getattr(info, "control_type", "") or ""
            ).strip().casefold()
            name = str(
                getattr(info, "name", "") or ""
            ).strip()

            if not name:
                return None

            if control_type not in {
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
            }:
                return None

            return {
                "event_uia_name": name,
                "event_uia_control_type": control_type,
                "event_uia_source": "windowhub_mouse_uia",
            }
        except Exception:
            return None

    @staticmethod
    def _topmost_belongs_to_windowhub(
        *,
        topmost: int,
        windowhub_hwnd: int,
        user32,
    ) -> bool:
        root = int(
            user32.GetAncestor(
                topmost,
                GA_ROOT,
            )
        )
        if root == windowhub_hwnd:
            return True

        # Owned dialogs/modal forms are separate top-level windows, so their
        # GA_ROOT is the dialog itself while GA_ROOTOWNER points to WindowHub.
        root_owner = int(
            user32.GetAncestor(
                topmost,
                GA_ROOTOWNER,
            )
        )
        return root_owner == windowhub_hwnd

    @classmethod
    def _windowhub_local_position(
        cls,
        screen_x: int,
        screen_y: int,
    ) -> tuple[int, int] | None:
        window = WindowHubEnvironmentAdapter._locate_windowhub_window()

        try:
            hwnd = int(
                getattr(window, "_hWnd", 0)
            )
        except (TypeError, ValueError):
            return None

        if hwnd <= 0:
            return None

        point = ctypes.wintypes.POINT(
            int(screen_x),
            int(screen_y),
        )

        user32 = ctypes.windll.user32
        topmost = int(
            user32.WindowFromPoint(point)
        )
        if topmost <= 0:
            return None

        if not cls._topmost_belongs_to_windowhub(
            topmost=topmost,
            windowhub_hwnd=hwnd,
            user32=user32,
        ):
            return None

        left = int(window.left)
        top = int(window.top)
        width = int(window.width)
        height = int(window.height)

        local_x = int(screen_x - left)
        local_y = int(screen_y - top)

        if not (
            0 <= local_x < width
            and 0 <= local_y < height
        ):
            return None

        return local_x, local_y
