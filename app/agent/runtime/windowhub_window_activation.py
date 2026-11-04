"""Explicitly authorized, bounded foreground activation for WindowHub.

Windows-only; never clicks, types, launches a process or selects arbitrary windows.
"""
from __future__ import annotations

import ctypes
import os
import time
from ctypes import wintypes

_ALLOWED_TITLES = frozenset({
    "Dodawanie nowej pozycji",
    "Wielkość okna",
    "Podstawowe parametry okna",
    "Parametry szklenia",
    "Parametry parapetu",
    "Parametry okuć",
})


def activate_windowhub_wizard(*, wait_seconds: float = 2.0) -> tuple[bool, str]:
    """Focus one existing visible Okna.exe wizard, or fail closed."""
    if os.name != "nt":
        return False, "Windows required"
    if os.environ.get("WH_REAL_WINDOWHUB") != "1" or os.environ.get("COMPUTER_USE_LIVE") != "1":
        return False, "Explicit live authorization required"

    try:
        import psutil
        user32 = ctypes.windll.user32
        user32.EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
        user32.EnumWindows.restype = wintypes.BOOL
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = ctypes.c_int
        user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        user32.SetForegroundWindow.restype = wintypes.BOOL
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.ShowWindow.restype = wintypes.BOOL

        candidates = []
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def inspect(hwnd, unused):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            if buffer.value.strip() not in _ALLOWED_TITLES:
                return True
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                process = psutil.Process(pid.value)
                if process.name().casefold() == "okna.exe":
                    candidates.append((hwnd, buffer.value))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            return True

        callback = callback_type(inspect)
        user32.EnumWindows(callback, 0)
        if len(candidates) != 1:
            return False, f"Expected one visible WindowHub wizard; found {len(candidates)}"

        hwnd, title = candidates[0]
        if user32.GetForegroundWindow() != hwnd:
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            user32.SetForegroundWindow(hwnd)
        deadline = time.monotonic() + max(0.0, min(wait_seconds, 5.0))
        while time.monotonic() <= deadline:
            if user32.GetForegroundWindow() == hwnd:
                return True, f"Activated WindowHub wizard: {title}"
            time.sleep(0.1)
        return False, f"Windows did not grant foreground focus to: {title}"
    except Exception as exc:
        return False, f"Activation unavailable: {type(exc).__name__}: {exc}"
