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

        foreground_handle, foreground_root_owner_handle = (
            self._foreground_window_context()
        )
        window_root_owner_handle = self._window_root_owner_handle(
            window_handle
        )

        screenshot = self.screenshot_engine.capture(
            window_rect
        )

        state = EnvironmentState(
            active_application=self.active_application,
            active_window_title=window_title,
            screen_width=screenshot.width,
            screen_height=screenshot.height,
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
                "window_focused": (
                    window_handle > 0
                    and foreground_handle == window_handle
                ),
                # GA_ROOTOWNER of the observed WindowHub HWND. The selected
                # form can be an owned dialog whose root owner is the app frame.
                "window_root_owner_handle": (
                    window_root_owner_handle
                    if window_root_owner_handle > 0
                    else None
                ),
                # Native handles remain local runtime metadata. They are
                # never projected into the NaviMind V2 world contract.
                "foreground_window_handle": (
                    foreground_handle if foreground_handle > 0 else None
                ),
                "foreground_root_owner_handle": (
                    foreground_root_owner_handle
                    if foreground_root_owner_handle > 0
                    else None
                ),
            },
        )

    @staticmethod
    def _foreground_window_context() -> tuple[int, int]:
        """Return foreground HWND and its GA_ROOTOWNER HWND, without UI text."""
        try:
            from ctypes import wintypes

            user32 = ctypes.WinDLL("user32", use_last_error=True)
            get_foreground = user32.GetForegroundWindow
            get_foreground.argtypes = ()
            get_foreground.restype = wintypes.HWND

            get_ancestor = user32.GetAncestor
            get_ancestor.argtypes = (wintypes.HWND, wintypes.UINT)
            get_ancestor.restype = wintypes.HWND

            foreground_value = get_foreground()
            foreground = WindowHubEnvironmentAdapter._native_handle_value(
                foreground_value
            )
            if foreground <= 0:
                return 0, 0

            # GA_ROOTOWNER = 3. This proves ownership without inspecting
            # titles, captions, text, control names, or field values.
            owner_value = get_ancestor(
                wintypes.HWND(foreground),
                3,
            )
            root_owner = WindowHubEnvironmentAdapter._native_handle_value(
                owner_value
            )
            return foreground, root_owner
        except Exception:
            return 0, 0

    @staticmethod
    def _window_root_owner_handle(window_handle: int) -> int:
        """Return GA_ROOTOWNER for the observed WindowHub HWND, fail-closed."""
        if (
            isinstance(window_handle, bool)
            or not isinstance(window_handle, int)
            or window_handle <= 0
        ):
            return 0
        try:
            from ctypes import wintypes

            user32 = ctypes.WinDLL("user32", use_last_error=True)
            get_ancestor = user32.GetAncestor
            get_ancestor.argtypes = (wintypes.HWND, wintypes.UINT)
            get_ancestor.restype = wintypes.HWND
            owner_value = get_ancestor(
                wintypes.HWND(window_handle),
                3,  # GA_ROOTOWNER
            )
            return WindowHubEnvironmentAdapter._native_handle_value(
                owner_value
            )
        except Exception:
            return 0

    @staticmethod
    def _native_handle_value(value) -> int:
        """Normalize ctypes HWND values and plain integer test doubles."""
        raw = getattr(value, "value", value)
        try:
            return int(raw or 0)
        except (TypeError, ValueError, OverflowError):
            return 0

    @classmethod
    def _is_foreground_window(cls, window_handle: int) -> bool:
        if window_handle <= 0:
            return False
        foreground, _root_owner = cls._foreground_window_context()
        return foreground == window_handle

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

        return max(
            candidates,
            key=lambda window: (
                int(window.width) * int(window.height),
            ),
        )
