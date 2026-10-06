from __future__ import annotations

import ctypes
import os
import threading
import time

from app.agent.learning.human_action_event import HumanActionEvent
from app.agent.learning.human_action_observer import (
    HumanActionCallback,
    HumanActionObserver,
)


class WindowsMouseObserver(HumanActionObserver):
    """
    Lightweight Windows mouse observer for LEARN mode.

    It watches only left-button transitions and cursor position. It does not
    record keyboard input or clipboard contents, which keeps the first learning
    implementation away from passwords and other typed secrets.

    Coordinates are transient event data used for semantic interpretation and
    are not persisted by the learning model.
    """

    VK_LBUTTON = 0x01

    def __init__(
        self,
        *,
        poll_interval_seconds: float = 0.03,
        debounce_seconds: float = 0.08,
    ) -> None:
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive.")
        if debounce_seconds < 0:
            raise ValueError("debounce_seconds must be non-negative.")

        self._poll_interval_seconds = poll_interval_seconds
        self._debounce_seconds = debounce_seconds
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._callback: HumanActionCallback | None = None

    def start(
        self,
        callback: HumanActionCallback,
    ) -> None:
        if os.name != "nt":
            raise RuntimeError("WindowsMouseObserver requires Windows.")

        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError("Windows mouse observer is already running.")

        self._callback = callback
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="agent-learn-mouse-observer",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)

        self._thread = None
        self._callback = None

    def _run(self) -> None:
        previous_pressed = False
        last_click = 0.0

        while not self._stop_event.is_set():
            pressed = bool(
                ctypes.windll.user32.GetAsyncKeyState(
                    self.VK_LBUTTON
                )
                & 0x8000
            )

            if pressed and not previous_pressed:
                now = time.monotonic()

                if (
                    now - last_click
                    >= self._debounce_seconds
                ):
                    x, y = self._cursor_position()
                    callback = self._callback

                    if callback is not None:
                        callback(
                            HumanActionEvent(
                                action_type="click",
                                x=x,
                                y=y,
                            )
                        )

                    last_click = now

            previous_pressed = pressed
            time.sleep(self._poll_interval_seconds)

    @staticmethod
    def _cursor_position() -> tuple[int, int]:
        point = ctypes.wintypes.POINT()
        if not ctypes.windll.user32.GetCursorPos(
            ctypes.byref(point)
        ):
            raise RuntimeError("Windows cursor position could not be read.")

        return int(point.x), int(point.y)
