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


class WindowHubMouseObserver(HumanActionObserver):
    """
    WindowHub-scoped mouse observer.

    The underlying Windows observer watches the left mouse button globally,
    while this adapter accepts only clicks whose topmost window belongs to the
    dynamically located WindowHub root. Coordinates are converted from screen
    space to WindowHub-local space before the semantic interpreter sees them.
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
            callback(
                HumanActionEvent(
                    action_type=event.action_type,
                    x=x,
                    y=y,
                    value=event.value,
                    metadata={
                        **dict(event.metadata or {}),
                        "scope": "WindowHub",
                    },
                )
            )

        return handle

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

        topmost = int(
            ctypes.windll.user32.WindowFromPoint(point)
        )
        if topmost <= 0:
            return None

        root = int(
            ctypes.windll.user32.GetAncestor(
                topmost,
                GA_ROOT,
            )
        )
        if root != hwnd:
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
