import ctypes
from ctypes import wintypes

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
from app.agent.environment.window_focus import is_target_window_focused
from app.runtime.execution.window.window_rect import (
    WindowRect,
)
from app.wh.vision.mss_screenshot_engine import (
    MSSScreenshotEngine,
)


class WindowHubEnvironmentAdapter(EnvironmentAdapter):
    """
    Bridges the Universal Agent Core environment contract
    with WindowHub's existing Windows/screenshot infrastructure.

    The WindowHub agent must never silently operate on whichever window
    happens to be foreground. The environment therefore resolves the
    current WindowHub top-level window explicitly and uses its handle,
    title and geometry for perception and execution.
    """

    def __init__(
        self,
        *,
        active_window_provider=None,
        active_application: str | None = None,
    ) -> None:
        # Kept for compatibility with existing callers/tests. The
        # WindowHub-specific locator is authoritative for this adapter.
        self.active_window_provider = active_window_provider
        self.active_application = (
            active_application
            or "WindowHub"
        )
        self.screenshot_engine = MSSScreenshotEngine()

    def observe(self) -> EnvironmentObservation:
        window = self._locate_windowhub_window()

        window_rect = WindowRect(
            left=int(window.left),
            top=int(window.top),
            width=int(window.width),
            height=int(window.height),
        )
        window_title = (window.title or "").strip() or None

        try:
            window_handle = int(
                getattr(window, "_hWnd", 0)
            )
        except (TypeError, ValueError):
            window_handle = 0

        screenshot = self.screenshot_engine.capture(
            window_rect
        )

        state = EnvironmentState(
            active_application=self.active_application,
            active_window_title=window_title,
            screen_width=screenshot.width,
            screen_height=screenshot.height,
        )

        foreground_window_handle = (
            self._foreground_window_handle()
        )
        foreground_root_owner_handle = (
            self._root_owner_window_handle(
                foreground_window_handle
            )
            if foreground_window_handle > 0
            else 0
        )

        return EnvironmentObservation(
            state=state,
            metadata={
                "source": "windowhub",
                "screenshot": screenshot,
                "window_rect": window_rect,
                "window_handle": (
                    window_handle
                    if window_handle > 0
                    else None
                ),
                # Some WindowHub-owned dialogs become the foreground HWND;
                # accept them only when their root owner is the located main window.
                "window_focused": bool(
                    window_handle > 0
                    and (
                        foreground_window_handle == window_handle
                        or foreground_root_owner_handle == window_handle
                    )
                ),
                "foreground_window_handle": (
                    foreground_window_handle
                    if foreground_window_handle > 0
                    else None
                ),
                "foreground_root_owner_handle": (
                    foreground_root_owner_handle
                    if foreground_root_owner_handle > 0
                    else None
                ),
            },
        )

    @staticmethod
    def _foreground_window_handle() -> int:
        try:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            get_foreground = user32.GetForegroundWindow
            get_foreground.restype = wintypes.HWND
            return int(get_foreground() or 0)
        except Exception:
            return 0

    @staticmethod
    def _root_owner_window_handle(window_handle: int) -> int:
        if window_handle <= 0:
            return 0

        try:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            get_ancestor = user32.GetAncestor
            get_ancestor.argtypes = (wintypes.HWND, wintypes.UINT)
            get_ancestor.restype = wintypes.HWND
            return int(get_ancestor(wintypes.HWND(window_handle), 3) or 0)
        except Exception:
            return 0

    @staticmethod
    def _is_foreground_window(window_handle: int) -> bool:
        return (
            window_handle > 0
            and WindowHubEnvironmentAdapter._foreground_window_handle()
            == window_handle
        )

    @staticmethod
    def _locate_windowhub_window():
        candidates = []

        for window in gw.getAllWindows():
            try:
                title = (window.title or "").strip()

                if not title.casefold().startswith("okna -"):
                    continue

                width = int(window.width)
                height = int(window.height)
                left = int(window.left)
                top = int(window.top)

                if width <= 0 or height <= 0:
                    continue

                if left < -10000 or top < -10000:
                    continue

                candidates.append(window)
            except Exception:
                continue

        if not candidates:
            raise RuntimeError(
                "WindowHub window not found."
            )

        # When several WindowHub documents/windows are open, use the one
        # the user actually brought to the foreground instead of silently
        # selecting a larger but unrelated Start/document window. If the
        # foreground belongs to an owned dialog, its root owner identifies
        # the corresponding WindowHub top-level window.
        foreground_handle = WindowHubEnvironmentAdapter._foreground_window_handle()
        root_owner_handle = (
            WindowHubEnvironmentAdapter._root_owner_window_handle(foreground_handle)
            if foreground_handle > 0
            else 0
        )
        foreground_candidates = []
        if foreground_handle > 0 or root_owner_handle > 0:
            for window in candidates:
                try:
                    hwnd = int(getattr(window, "_hWnd", 0))
                except (TypeError, ValueError):
                    continue
                if hwnd > 0 and hwnd in (foreground_handle, root_owner_handle):
                    foreground_candidates.append(window)

        selection_pool = foreground_candidates or candidates
        return max(
            selection_pool,
            key=lambda window: (
                int(window.width) * int(window.height),
            ),
        )
