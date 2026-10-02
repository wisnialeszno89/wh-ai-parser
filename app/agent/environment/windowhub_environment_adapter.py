from app.agent.environment.environment_adapter import (
    EnvironmentAdapter,
)
from app.agent.environment.environment_observation import (
    EnvironmentObservation,
)
from app.agent.environment.environment_state import (
    EnvironmentState,
)
from app.agent.environment.windows_active_window_provider import (
    WindowsActiveWindowProvider,
)
from app.wh.vision.mss_screenshot_engine import (
    MSSScreenshotEngine,
)


class WindowHubEnvironmentAdapter(EnvironmentAdapter):
    """
    Bridges the Universal Agent Core environment contract
    with WindowHub's existing Windows/screenshot infrastructure.
    """

    def __init__(
        self,
        *,
        active_window_provider: WindowsActiveWindowProvider | None = None,
        active_application: str | None = None,
    ) -> None:
        self.active_window_provider = (
            active_window_provider
            or WindowsActiveWindowProvider()
        )
        self.active_application = (
            active_application
            or "WindowHub"
        )
        self.screenshot_engine = MSSScreenshotEngine()

    def observe(self) -> EnvironmentObservation:
        window_rect, window_title = (
            self.active_window_provider.get()
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

        window_handle = None
        if __import__("os").name == "nt":
            import ctypes

            try:
                handle = int(
                    ctypes.windll.user32.GetForegroundWindow()
                )
            except Exception:
                handle = 0

            if handle > 0:
                window_handle = handle

        return EnvironmentObservation(
            state=state,
            metadata={
                "source": "windowhub",
                "screenshot": screenshot,
                "window_rect": window_rect,
                "window_handle": window_handle,
            },
        )
