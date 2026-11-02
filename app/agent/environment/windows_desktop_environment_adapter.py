"""Observe the active Windows desktop window through native Win32 APIs."""

from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass
from ctypes import wintypes

from app.agent.environment.environment_adapter import EnvironmentAdapter
from app.agent.environment.environment_observation import EnvironmentObservation
from app.agent.environment.environment_state import EnvironmentState
from app.runtime.execution.window.window_rect import WindowRect
from app.wh.vision.mss_screenshot_engine import MSSScreenshotEngine


@dataclass(frozen=True)
class ForegroundWindowSnapshot:
    """Local-only metadata for one foreground top-level Windows window."""

    handle: int
    title: str | None
    rect: WindowRect
    active_application: str | None
    root_owner_handle: int | None


class WindowsDesktopEnvironmentAdapter(EnvironmentAdapter):
    """Capture the current foreground window, independent of application identity.

    The adapter deliberately follows the user's active top-level window. It does
    not search for WindowHub or silently switch to another application.
    """

    def __init__(
        self,
        *,
        screenshot_engine=None,
        snapshot_provider=None,
    ) -> None:
        self.screenshot_engine = screenshot_engine or MSSScreenshotEngine()
        self._snapshot_provider = (
            snapshot_provider or self._capture_foreground_window
        )

    def observe(self) -> EnvironmentObservation:
        snapshot = self._snapshot_provider()
        if not isinstance(snapshot, ForegroundWindowSnapshot):
            raise TypeError("windows_desktop_snapshot_invalid")
        if (
            isinstance(snapshot.handle, bool)
            or not isinstance(snapshot.handle, int)
            or snapshot.handle <= 0
        ):
            raise RuntimeError("windows_desktop_foreground_window_missing")

        rect = snapshot.rect
        if (
            rect is None
            or int(rect.width) <= 0
            or int(rect.height) <= 0
        ):
            raise RuntimeError("windows_desktop_foreground_bounds_invalid")

        screenshot = self.screenshot_engine.capture(rect)
        root_owner = snapshot.root_owner_handle
        if (
            isinstance(root_owner, bool)
            or not isinstance(root_owner, int)
            or root_owner <= 0
        ):
            root_owner = None

        application = (
            snapshot.active_application.strip()
            if isinstance(snapshot.active_application, str)
            and snapshot.active_application.strip()
            else "unknown"
        )
        title = (
            snapshot.title.strip()
            if isinstance(snapshot.title, str) and snapshot.title.strip()
            else None
        )

        state = EnvironmentState(
            active_application=application,
            active_window_title=title,
            screen_width=int(screenshot.width),
            screen_height=int(screenshot.height),
        )
        return EnvironmentObservation(
            state=state,
            metadata={
                "source": "windows_desktop",
                "screenshot": screenshot,
                "window_rect": rect,
                "window_handle": snapshot.handle,
                "window_focused": True,
                "window_root_owner_handle": root_owner,
                "foreground_window_handle": snapshot.handle,
                "foreground_root_owner_handle": root_owner,
            },
        )

    @classmethod
    def _capture_foreground_window(cls) -> ForegroundWindowSnapshot:
        if os.name != "nt":
            raise RuntimeError("windows_desktop_requires_windows")

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        get_foreground = user32.GetForegroundWindow
        get_foreground.argtypes = ()
        get_foreground.restype = wintypes.HWND

        hwnd_value = get_foreground()
        handle = cls._native_handle_value(hwnd_value)
        if handle <= 0:
            raise RuntimeError("windows_desktop_foreground_window_missing")
        hwnd = wintypes.HWND(handle)

        get_rect = user32.GetWindowRect
        get_rect.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.RECT))
        get_rect.restype = wintypes.BOOL
        native_rect = wintypes.RECT()
        if not get_rect(hwnd, ctypes.byref(native_rect)):
            raise RuntimeError("windows_desktop_window_rect_unavailable")

        width = int(native_rect.right - native_rect.left)
        height = int(native_rect.bottom - native_rect.top)
        if width <= 0 or height <= 0:
            raise RuntimeError("windows_desktop_foreground_window_not_visible")

        get_text_length = user32.GetWindowTextLengthW
        get_text_length.argtypes = (wintypes.HWND,)
        get_text_length.restype = ctypes.c_int
        get_text = user32.GetWindowTextW
        get_text.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
        get_text.restype = ctypes.c_int
        title_length = max(0, min(int(get_text_length(hwnd)), 4_095))
        title = None
        if title_length:
            title_buffer = ctypes.create_unicode_buffer(title_length + 1)
            copied = int(get_text(hwnd, title_buffer, len(title_buffer)))
            title = title_buffer.value.strip() if copied > 0 else None
            title = title or None

        get_thread_process_id = user32.GetWindowThreadProcessId
        get_thread_process_id.argtypes = (
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        )
        get_thread_process_id.restype = wintypes.DWORD
        process_id = wintypes.DWORD(0)
        get_thread_process_id(hwnd, ctypes.byref(process_id))
        application = cls._process_name(
            kernel32,
            int(process_id.value),
        )

        get_ancestor = user32.GetAncestor
        get_ancestor.argtypes = (wintypes.HWND, wintypes.UINT)
        get_ancestor.restype = wintypes.HWND
        owner_value = get_ancestor(hwnd, 3)  # GA_ROOTOWNER
        root_owner = cls._native_handle_value(owner_value)

        return ForegroundWindowSnapshot(
            handle=handle,
            title=title,
            rect=WindowRect(
                left=int(native_rect.left),
                top=int(native_rect.top),
                width=width,
                height=height,
            ),
            active_application=application,
            root_owner_handle=root_owner if root_owner > 0 else None,
        )

    @classmethod
    def _process_name(cls, kernel32, process_id: int) -> str | None:
        if process_id <= 0:
            return None

        open_process = kernel32.OpenProcess
        open_process.argtypes = (
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        )
        open_process.restype = wintypes.HANDLE

        query_image = kernel32.QueryFullProcessImageNameW
        query_image.argtypes = (
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        )
        query_image.restype = wintypes.BOOL

        close_handle = kernel32.CloseHandle
        close_handle.argtypes = (wintypes.HANDLE,)
        close_handle.restype = wintypes.BOOL

        process = open_process(0x1000, False, process_id)  # QUERY_LIMITED_INFORMATION
        if not process:
            return None
        try:
            buffer = ctypes.create_unicode_buffer(4_096)
            length = wintypes.DWORD(len(buffer))
            if not query_image(process, 0, buffer, ctypes.byref(length)):
                return None
            path = buffer.value.strip()
            return os.path.basename(path) or None
        finally:
            close_handle(process)

    @staticmethod
    def _native_handle_value(value) -> int:
        raw = getattr(value, "value", value)
        try:
            return int(raw or 0)
        except (TypeError, ValueError, OverflowError):
            return 0
