"""Generic desktop Explorer window selection and focus, without GUI clicks.

Focus only an unambiguous, running, visible and non-minimized application
window. A title fragment may narrow candidates, but never overrides process
identity. No process launches, no documents chosen by ranking.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import time


def select_unique_window(
    windows: list[dict],
    *,
    process: str,
    title_contains: str = "",
    foreground_hwnd: int | None = None,
    prefer_unique_offer: bool = False,
) -> tuple[int | None, str]:
    expected = process.strip().casefold()
    if not expected:
        return None, "process_missing"
    matches = [
        item for item in windows
        if item.get("process", "").casefold() == expected
        and item.get("visible") is True
        and item.get("minimized") is False
        and isinstance(item.get("hwnd"), int)
        and not isinstance(item.get("hwnd"), bool)
        and item["hwnd"] > 0
        and (
            not title_contains
            or title_contains.casefold() in item.get("title", "").casefold()
        )
    ]
    if not matches:
        return None, "no_matching_visible_window"
    if len(matches) == 1:
        return matches[0]["hwnd"], "unique_match"
    foreground = [item for item in matches if item["hwnd"] == foreground_hwnd]
    if len(foreground) == 1:
        return foreground[0]["hwnd"], "already_foreground_match"
    if prefer_unique_offer and expected == "okna.exe":
        # Prefer one offer only over known idle home windows. An unfamiliar
        # window/dialog might be modal and must never be bypassed by guessing.
        offers = [
            item for item in matches
            if item.get("title", "").strip().casefold().startswith("okna - ofr/")
        ]
        idle_titles = {"okna", "okna - start1", "okna -"}
        rest = [item for item in matches if item not in offers]
        if len(offers) == 1 and all(
            item.get("title", "").strip().casefold() in idle_titles
            for item in rest
        ):
            return offers[0]["hwnd"], "unique_offer_over_idle_home"
    return None, "ambiguous_windows_" + str(len(matches))


def focus_application_for_exploration(
    *, process: str, title_contains: str = "", timeout: float = 2.0,
    prefer_unique_offer: bool = False
) -> tuple[bool, str]:
    """Focus existing process window; verify process/HWND after Windows focus."""
    if os.name != "nt":
        return False, "windows_required"
    try:
        import psutil
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        callback_type = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
        )
        user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
        user32.EnumWindows.restype = wintypes.BOOL
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.IsIconic.argtypes = [wintypes.HWND]
        user32.IsIconic.restype = wintypes.BOOL
        user32.GetForegroundWindow.argtypes = []
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = ctypes.c_int
        user32.GetWindowTextW.argtypes = [
            wintypes.HWND, wintypes.LPWSTR, ctypes.c_int
        ]
        user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND, ctypes.POINTER(wintypes.DWORD)
        ]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        windows = []

        def inspect(hwnd, unused):
            if not user32.IsWindowVisible(hwnd):
                return True
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                exe = psutil.Process(pid.value).name().casefold()
            except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
                return True
            if exe != process.casefold():
                return True
            length = min(1024, max(0, user32.GetWindowTextLengthW(hwnd)))
            buf = ctypes.create_unicode_buffer(length + 1)
            if length:
                user32.GetWindowTextW(hwnd, buf, length + 1)
            windows.append({
                "hwnd": int(hwnd),
                "process": exe,
                "title": buf.value.strip(),
                "visible": True,
                "minimized": bool(user32.IsIconic(hwnd)),
            })
            return True

        callback = callback_type(inspect)
        user32.EnumWindows(callback, 0)
        foreground = int(user32.GetForegroundWindow() or 0)
        hwnd, status = select_unique_window(
            windows, process=process, title_contains=title_contains,
            foreground_hwnd=foreground,
            prefer_unique_offer=prefer_unique_offer,
        )
        if hwnd is None:
            return False, status
        from app.agent.runtime.windowhub_window_activation import (
            _focus_existing_window,
        )
        if not _focus_existing_window(user32, wintypes.HWND(hwnd)):
            return False, "windows_focus_denied"
        deadline = time.monotonic() + min(max(timeout, 0), 5)
        while time.monotonic() <= deadline:
            if int(user32.GetForegroundWindow() or 0) == hwnd:
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(
                    wintypes.HWND(hwnd), ctypes.byref(pid)
                )
                if psutil.Process(pid.value).name().casefold() == process.casefold():
                    return True, "verified_foreground_" + status
                return False, "foreground_process_changed"
            time.sleep(.1)
        return False, "focus_not_verified"
    except Exception as exc:
        return False, "activation_error_" + type(exc).__name__
