from __future__ import annotations

import ctypes

import pygetwindow as gw

from app.agent.environment.environment_adapter import (
    EnvironmentAdapter,
)
from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.runtime.execution.window.window_rect import (
    WindowRect,
)
from app.wh.vision.mss_screenshot_engine import (
    MSSScreenshotEngine,
)


class WindowsDesktopEnvironmentAdapter(EnvironmentAdapter):
    """
    Generic Windows desktop environment.

    Unlike WindowHubEnvironmentAdapter this adapter does not assume any
    application name or business domain. It observes the current active
    top-level window and exposes its geometry, handle, focus state and
    screenshot to the Universal Agent Core.
    """

    def __init__(
        self,
        *,
        active_window_provider=None,
        active_application: str = "WindowsDesktop",
    ) -> None:
        self.active_window_provider = active_window_provider
        self.active_application = active_application
        self.screenshot_engine = MSSScreenshotEngine()

    def observe(self) -> EnvironmentObservation:
        window = self._get_active_window()

        rect = WindowRect(
            left=int(window.left),
            top=int(window.top),
            width=int(window.width),
            height=int(window.height),
        )

        if rect.width <= 0 or rect.height <= 0:
            raise RuntimeError(
                "Active Windows desktop window has invalid bounds."
            )

        title = (
            (getattr(window, "title", None) or "").strip()
            or None
        )

        try:
            window_handle = int(
                getattr(window, "_hWnd", 0)
            )
        except (TypeError, ValueError):
            window_handle = 0

        screenshot = self.screenshot_engine.capture(rect)

        foreground_handle = self._foreground_window_handle()

        foreground_owner = (
            self._root_owner_window_handle(
                foreground_handle
            )
            if foreground_handle > 0
            else 0
        )

        return EnvironmentObservation(
            state=EnvironmentState(
                active_application=self.active_application,
                active_window_title=title,
                screen_width=screenshot.width,
                screen_height=screenshot.height,
            ),
            metadata={
                "source": "windows_desktop",
                "screenshot": screenshot,
                "window_rect": rect,
                "window_handle": (
                    window_handle
                    if window_handle > 0
                    else None
                ),
                "window_focused": (
                    foreground_handle > 0
                    and foreground_handle == window_handle
                ),
                "foreground_window_handle": (
                    foreground_handle
                    if foreground_handle > 0
                    else None
                ),
                "foreground_root_owner_handle": (
                    foreground_owner
                    if foreground_owner > 0
                    else None
                ),
            },
        )

    def _get_active_window(self):
        if self.active_window_provider is not None:
            getter = getattr(
                self.active_window_provider,
                "get",
                None,
            )

            if not callable(getter):
                raise RuntimeError(
                    "Configured active_window_provider has no get() method."
                )

            result = getter()

            if isinstance(result, tuple):
                window_rect, title = result

                class _ProviderWindow:
                    pass

                window = _ProviderWindow()
                window.left = window_rect.left
                window.top = window_rect.top
                window.width = window_rect.width
                window.height = window_rect.height
                window.title = title
                window._hWnd = 0
                return window

            return result

        window = gw.getActiveWindow()

        if window is None:
            raise RuntimeError(
                "No active Windows desktop window is available."
            )

        return window

    @staticmethod
    def _foreground_window_handle() -> int:
        try:
            return int(
                ctypes.windll.user32.GetForegroundWindow()
            )
        except Exception:
            return 0

    @staticmethod
    def _root_owner_window_handle(window_handle: int) -> int:
        if window_handle <= 0:
            return 0

        try:
            return int(
                ctypes.windll.user32.GetAncestor(
                    int(window_handle),
                    3,
                )
            )
        except Exception:
            return 0
