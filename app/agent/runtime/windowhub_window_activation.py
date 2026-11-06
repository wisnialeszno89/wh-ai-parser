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



def _focus_existing_window(user32, hwnd) -> bool:
    """Best-effort automatic Win32 foreground transfer for one verified HWND.

    Attach input queues only temporarily; never synthesize keys or mouse
    events. Windows may still deny focus, in which case return False.
    """
    if user32.GetForegroundWindow() == hwnd:
        return True
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    user32.SetForegroundWindow(hwnd)
    if user32.GetForegroundWindow() == hwnd:
        return True

    kernel32 = ctypes.windll.kernel32
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.AttachThreadInput.argtypes = [
        wintypes.DWORD, wintypes.DWORD, wintypes.BOOL,
    ]
    user32.AttachThreadInput.restype = wintypes.BOOL
    current_thread = kernel32.GetCurrentThreadId()
    foreground = user32.GetForegroundWindow()
    foreground_thread = (
        user32.GetWindowThreadProcessId(foreground, None)
        if foreground else 0
    )
    target_thread = user32.GetWindowThreadProcessId(hwnd, None)
    attached = []
    try:
        for thread_id in (foreground_thread, target_thread):
            if thread_id and thread_id != current_thread and thread_id not in attached:
                if not user32.AttachThreadInput(current_thread, thread_id, True):
                    return False
                attached.append(thread_id)
        user32.BringWindowToTop.argtypes = [wintypes.HWND]
        user32.BringWindowToTop.restype = wintypes.BOOL
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        return user32.GetForegroundWindow() == hwnd
    finally:
        for thread_id in reversed(attached):
            user32.AttachThreadInput(current_thread, thread_id, False)


def activate_windowhub_wizard(*, wait_seconds: float = 2.0, include_workspace: bool = False) -> tuple[bool, str]:
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
            title = buffer.value.strip()
            is_wizard = title in _ALLOWED_TITLES
            is_workflow = (
                title in {"Właściwości dokumentu", "Zakładanie nowego klienta"}
                or title.startswith("Okna - Start1")
                or title.startswith("Okna - OFR/")
            )
            if not is_wizard and not (include_workspace and is_workflow):
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
        if include_workspace:
            # Prefer a unique active wizard/document dialog over the main window.
            dialogs = [
                item for item in candidates
                if item[1] in _ALLOWED_TITLES or item[1] in {"Właściwości dokumentu", "Zakładanie nowego klienta"}
            ]
            if dialogs:
                candidates = dialogs
            else:
                start = [item for item in candidates if item[1].startswith("Okna - Start1")]
                documents = [item for item in candidates if item[1].startswith("Okna - OFR/")]
                candidates = start if start else documents
        if len(candidates) != 1:
            return False, f"Expected one unambiguous WindowHub workflow window; found {len(candidates)}"

        hwnd, title = candidates[0]
        # The agent must activate WindowHub automatically. Do not request
        # manual title-bar clicks; never proceed without verified foreground.
        _focus_existing_window(user32, hwnd)
        deadline = time.monotonic() + max(0.0, min(wait_seconds, 5.0))
        while time.monotonic() <= deadline:
            if user32.GetForegroundWindow() == hwnd:
                return True, f"Activated WindowHub wizard: {title}"
            time.sleep(0.1)
        return False, f"Windows did not grant foreground focus to: {title}"
    except Exception as exc:
        return False, f"Activation unavailable: {type(exc).__name__}: {exc}"


def activate_windowhub_workflow_window(*, wait_seconds: float = 3.0) -> tuple[bool, str]:
    """Activate one observed WindowHub dialog or start/document workspace."""
    return activate_windowhub_wizard(
        wait_seconds=wait_seconds,
        include_workspace=True,
    )


def activate_unique_windowhub_offer_document(*, wait_seconds: float = 3.0) -> tuple[bool, str]:
    """Focus a *unique* visible Okna.exe offer document, never a wizard or Start1.

    Strictly read-only with respect to business data: this operation transfers
    focus only. If multiple offers are open, fail rather than guess which one.
    """
    if os.name != "nt":
        return False, "Windows required"
    if os.environ.get("WH_REAL_WINDOWHUB") != "1" or os.environ.get("COMPUTER_USE_LIVE") != "1":
        return False, "Explicit activation authorization required"
    try:
        import psutil
        user32 = ctypes.windll.user32
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
        user32.EnumWindows.restype = wintypes.BOOL
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = ctypes.c_int
        user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        user32.SetForegroundWindow.restype = wintypes.BOOL
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.ShowWindow.restype = wintypes.BOOL
        found = []

        def inspect(hwnd, unused):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            if not buffer.value.strip().casefold().startswith("okna - ofr/"):
                return True
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try:
                if psutil.Process(pid.value).name().casefold() == "okna.exe":
                    found.append(int(hwnd))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            return True

        callback = callback_type(inspect)
        user32.EnumWindows(callback, 0)
        if len(found) != 1:
            return False, f"Expected exactly one visible Okna.exe offer document; found {len(found)}"
        hwnd = found[0]
        _focus_existing_window(user32, hwnd)
        deadline = time.monotonic() + max(0.0, min(wait_seconds, 5.0))
        while time.monotonic() <= deadline:
            if user32.GetForegroundWindow() == hwnd:
                return True, "Unique WindowHub offer document activated"
            time.sleep(0.1)
        return False, "WindowHub offer document did not gain foreground focus"
    except Exception as exc:
        return False, f"Offer activation unavailable: {type(exc).__name__}"
