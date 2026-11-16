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


def unique_observable_window(candidates) -> int | None:
    """Read-only focus eligibility: exactly one unique process-scoped HWND."""
    if not isinstance(candidates, (list, tuple)):
        return None
    valid = []
    for row in candidates:
        if not isinstance(row, (tuple, list)) or len(row) != 3:
            return None
        handle, visible, minimized = row
        if (isinstance(handle, bool) or not isinstance(handle, int)
                or handle <= 0 or visible is not True):
            continue
        if minimized is True:
            continue
        valid.append(handle)
    return valid[0] if len(valid) == 1 else None


def activate_unique_windowhub_for_inspection() -> tuple[bool, str]:
    """Focus one visible Okna.exe top-level window of ANY title, inspection only.

    This is intentionally NOT wired to execute/think mode. Never starts an
    application, clicks a control or selects among multiple windows.
    """
    import os
    if os.name != "nt":
        return False, "windows_required"
    import ctypes
    from ctypes import wintypes
    try:
        import psutil
        from app.agent.runtime.windowhub_window_activation import _focus_existing_window
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        callback_type = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
        )
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.IsIconic.argtypes = [wintypes.HWND]
        user32.IsIconic.restype = wintypes.BOOL
        user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND, ctypes.POINTER(wintypes.DWORD)
        ]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.GetForegroundWindow.argtypes = []
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        user32.SetForegroundWindow.restype = wintypes.BOOL
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.ShowWindow.restype = wintypes.BOOL
        windows = []
        def visit(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                if pid.value > 0 and psutil.Process(pid.value).name().casefold() == "okna.exe":
                    windows.append((int(hwnd), True, bool(user32.IsIconic(hwnd))))
            except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
                pass
            return True

        callback = callback_type(visit)
        user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
        user32.EnumWindows.restype = wintypes.BOOL
        user32.EnumWindows(callback, 0)
        hwnd = unique_observable_window(windows)
        if hwnd is None:
            return False, "not_one_unique_visible_unminimized_okna_window"
        if not _focus_existing_window(user32, hwnd):
            return False, "windows_refused_foreground_focus"
        if int(user32.GetForegroundWindow() or 0) != hwnd:
            return False, "foreground_did_not_match_unique_window"
        return True, "unique_unknown_windowhub_focused_for_read_only_inspection"
    except Exception as exc:
        return False, "inspection_focus_unavailable_" + type(exc).__name__
