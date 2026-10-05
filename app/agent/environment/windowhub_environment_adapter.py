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
                "window_focused": self._is_foreground_window(
                    window_handle
                ),
            },
        )

    @staticmethod
    def _is_foreground_window(window_handle: int) -> bool:
        if window_handle <= 0:
            return False

        try:
            foreground = int(
                ctypes.windll.user32.GetForegroundWindow()
            )
        except Exception:
            return False

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
