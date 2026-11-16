"""Observe an unfamiliar WindowHub foreground title without focusing anything.

A distinct, more permissive *inspection* boundary, not an execution policy.
"""
from __future__ import annotations


def inspect_current_windowhub_foreground(*, capture=None) -> bool:
    """Allow read-only discovery when foreground PID belongs to Okna.exe."""
    if capture is not None:
        try:
            app, valid_foreground = capture()
        except Exception:
            return False
        return str(app).casefold() == "okna.exe" and valid_foreground is True

    import os
    if os.name != "nt":
        return False
    import ctypes
    from ctypes import wintypes
    try:
        import psutil
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.GetForegroundWindow.argtypes = []
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND, ctypes.POINTER(wintypes.DWORD)
        ]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value <= 0:
            return False
        return psutil.Process(pid.value).name().casefold() == "okna.exe"
    except (OSError, ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
        return False
