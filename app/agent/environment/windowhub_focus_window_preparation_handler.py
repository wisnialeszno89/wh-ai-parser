from __future__ import annotations

import ctypes
import time
from typing import Callable

import pygetwindow as gw

from app.agent.environment.environment_preparation import (
    EnvironmentPreparation,
)
from app.agent.environment.environment_preparation_result import (
    EnvironmentPreparationResult,
)
from app.agent.environment.environment_preparation_strategy import (
    EnvironmentPreparationStrategy,
)
from app.agent.environment.environment_preparation_strategy_handler import (
    EnvironmentPreparationStrategyHandler,
)


class WindowHubFocusWindowPreparationHandler(
    EnvironmentPreparationStrategyHandler
):
    """
    Concrete Windows preparation handler for WindowHub focus.

    The handler resolves the WindowHub top-level window semantically from
    its title, activates it, and verifies that Windows actually granted
    foreground focus before reporting success.
    """

    def __init__(
        self,
        *,
        window_provider: Callable[[], object] | None = None,
        sleep_seconds: float = 0.15,
    ) -> None:
        self._window_provider = (
            window_provider
            or self._locate_windowhub_window
        )
        self._sleep_seconds = sleep_seconds

    @property
    def strategy(
        self,
    ) -> EnvironmentPreparationStrategy:
        return EnvironmentPreparationStrategy.FOCUS_WINDOW

    def execute(
        self,
        preparation: EnvironmentPreparation,
    ) -> EnvironmentPreparationResult:
        if (
            preparation.target_application
            and preparation.target_application.casefold()
            != "windowhub"
        ):
            return EnvironmentPreparationResult(
                success=False,
                reason=(
                    "WindowHub focus handler received an "
                    "unexpected target application."
                ),
                metadata={
                    "target_application": (
                        preparation.target_application
                    ),
                },
            )

        try:
            window = self._window_provider()
        except Exception as exc:
            return EnvironmentPreparationResult(
                success=False,
                reason=f"WindowHub window could not be located: {exc}",
            )

        try:
            if callable(getattr(window, "isMinimized", None)) and window.isMinimized:
                restore = getattr(window, "restore", None)
                if callable(restore):
                    restore()

            activate = getattr(window, "activate", None)
            if not callable(activate):
                raise RuntimeError(
                    "WindowHub window does not expose activation."
                )

            activate()

            if self._sleep_seconds > 0:
                time.sleep(self._sleep_seconds)

            handle = int(getattr(window, "_hWnd", 0))
        except Exception as exc:
            return EnvironmentPreparationResult(
                success=False,
                reason=f"WindowHub focus activation failed: {exc}",
            )

        if handle <= 0:
            return EnvironmentPreparationResult(
                success=False,
                reason="WindowHub window has no valid handle after activation.",
            )

        try:
            foreground = int(
                ctypes.windll.user32.GetForegroundWindow()
            )
        except Exception as exc:
            return EnvironmentPreparationResult(
                success=False,
                reason=f"Could not verify WindowHub foreground focus: {exc}",
            )

        focused = foreground == handle

        return EnvironmentPreparationResult(
            success=focused,
            reason=(
                "WindowHub window focused successfully."
                if focused
                else "WindowHub window activation did not grant foreground focus."
            ),
            metadata={
                "target_application": "WindowHub",
                "window_handle": handle,
                "foreground_handle": foreground,
                "focused": focused,
            },
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
            raise RuntimeError("WindowHub window not found.")

        return max(
            candidates,
            key=lambda window: (
                int(window.width) * int(window.height),
            ),
        )
