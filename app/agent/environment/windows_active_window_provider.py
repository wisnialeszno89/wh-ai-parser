import pygetwindow as gw

from app.runtime.execution.window.window_rect import (
    WindowRect,
)


class WindowsActiveWindowProvider:
    """
    Provides the geometry and title of the current foreground window.
    """

    def get(self) -> tuple[WindowRect, str | None]:
        window = gw.getActiveWindow()

        if window is None:
            raise RuntimeError(
                "No active window is available."
            )

        rect = WindowRect(
            left=int(window.left),
            top=int(window.top),
            width=int(window.width),
            height=int(window.height),
        )

        title = getattr(
            window,
            "title",
            None,
        )

        return rect, title
