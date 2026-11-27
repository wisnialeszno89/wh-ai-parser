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


def _focus_for_draft(user32, hwnd, *, still_current) -> bool:
    """Transfer foreground without attaching to the other thread's input queue."""
    user32.GetForegroundWindow.restype = wintypes.HWND
    if not still_current():
        return False
    if user32.GetForegroundWindow() == hwnd:
        return True
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsIconic.restype = wintypes.BOOL
    if user32.IsIconic(hwnd):
        user32.ShowWindowAsync.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.ShowWindowAsync.restype = wintypes.BOOL
        user32.ShowWindowAsync(hwnd, 9)  # SW_RESTORE
    if not still_current():
        return False
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    return bool(user32.SetForegroundWindow(hwnd))



def activate_windowhub_wizard(*, wait_seconds: float = 2.0, include_workspace: bool = False, prefer_start: bool = False,
                              still_current=None) -> tuple[bool, str]:
    """Focus one existing visible Okna.exe wizard, or fail closed."""
    if os.name != "nt":
        return False, "Windows required"
    if os.environ.get("WH_REAL_WINDOWHUB") != "1" or os.environ.get("COMPUTER_USE_LIVE") != "1":
        return False, "Explicit live authorization required"

    try:
        from app.agent.environment.windows_desktop_environment_adapter import (
            WindowsDesktopEnvironmentAdapter,
        )

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
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
                or title.startswith("Okna - ZLC/")
            )
            if not is_wizard and not (include_workspace and is_workflow):
                return True
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            application = WindowsDesktopEnvironmentAdapter._process_name(kernel32, pid.value)
            if application and application.replace("\\", "/").rsplit("/", 1)[-1].casefold() == "okna.exe":
                candidates.append((hwnd, title))
            return True

        callback = callback_type(inspect)
        user32.EnumWindows(callback, 0)
        if include_workspace and prefer_start:
            # Use the real Start1 workspace, not a background tile from an offer.
            # No document is closed or modified during this selection.
            candidates = [
                item for item in candidates
                if item[1].strip().casefold() == "okna - start1"
            ]
        elif include_workspace:
            # Preserve the specific WindowHub stage when it already has focus;
            # a background Start1 must not override an open offer document.
            foreground_hwnd = user32.GetForegroundWindow()
            foreground_match = [
                item for item in candidates if item[0] == foreground_hwnd
            ]
            if len(foreground_match) == 1:
                candidates = foreground_match
            else:
                dialogs = [
                    item for item in candidates
                    if item[1] in _ALLOWED_TITLES
                    or item[1] in {"Właściwości dokumentu", "Zakładanie nowego klienta"}
                ]
                documents = [
                    item for item in candidates
                    if item[1].startswith("Okna - OFR/")
                    or item[1].startswith("Okna - ZLC/")
                ]
                start = [
                    item for item in candidates
                    if item[1].startswith("Okna - Start1")
                ]
                # A document outranks Start1, provided it is unique. Multiple
                # candidate dialogs/documents remain ambiguous and fail closed.
                candidates = dialogs or documents or start
        if len(candidates) != 1:
            return False, f"Expected one unambiguous WindowHub workflow window; found {len(candidates)}"

        hwnd, title = candidates[0]
        # The agent must activate WindowHub automatically. Do not request
        # manual title-bar clicks; never proceed without verified foreground.
        if still_current is None:
            _focus_existing_window(user32, hwnd)
        else:
            _focus_for_draft(user32, hwnd, still_current=still_current)
        deadline = time.monotonic() + max(0.0, min(wait_seconds, 5.0))
        while time.monotonic() <= deadline:
            if still_current is not None and not still_current():
                return False, "start1_navigation_cancelled"
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


def unique_start1_navigation_candidate(controls):
    """Choose one exact native UIA Start1 navigation control; never by location.

    Input is local structural metadata. This function cannot click or inspect
    customer data and does not accept a generic unidentified toolbar icon.
    """
    matches = []
    for item in controls:
        if (
            item.get("name", "").strip().casefold() == "start1"
            and item.get("kind") in {"button", "tabitem"}
            and item.get("enabled") is True
            and item.get("visible") is True
            and isinstance(item.get("automation_id"), str)
            and bool(item["automation_id"].strip())
            and bool(item.get("runtime_id"))
        ):
            matches.append(item)
    return matches[0] if len(matches) == 1 else None


def _activate_start1_via_unique_navigation(*, wait_seconds: float, still_current) -> tuple[bool, str]:
    """After local Resume, select one verified UIA Start1 tab/button in Okna.

    No guessed icon coordinate or keyboard shortcut. Selecting a tab does not
    close or save the current offer; a modal dialog blocks this path.
    """
    if os.name != "nt" or (
        os.environ.get("WH_REAL_WINDOWHUB") != "1"
        or os.environ.get("COMPUTER_USE_LIVE") != "1"
    ):
        return False, "start1_navigation_live_permission_missing"
    try:
        from pywinauto import Desktop
        from app.agent.environment.windows_desktop_environment_adapter import (
            WindowsDesktopEnvironmentAdapter,
        )
        from app.agent.perception.windowhub_ui_automation_provider import (
            WindowHubUIAutomationProvider,
        )
        adapter = WindowsDesktopEnvironmentAdapter()
        foreground = adapter._capture_foreground_window()
        inventory = adapter._capture_visible_windows(
            foreground.handle, snapshot=foreground,
        )
        # Only a unique WindowHub main frame, not arbitrary editor dialogs.
        frames = [
            w for w in inventory
            if (w.application or "").replace(chr(92), "/").rsplit("/", 1)[-1].casefold() == "okna.exe"
            and (w.title or "").strip().casefold().startswith("okna - ")
            and w.is_visible and not w.is_minimized
        ]
        if len(frames) != 1:
            return False, "start1_main_frame_not_unique"
        frame = frames[0]
        desktop = Desktop(backend="uia")
        root = desktop.window(handle=frame.handle).wrapper_object()
        if (root.window_text() or "").strip() != (frame.title or "").strip():
            return False, "start1_main_frame_changed"
        wrappers = tuple(root.descendants())[:2500]
        controls = []
        for wrapper in wrappers:
            try:
                info = wrapper.element_info
                kind = str(info.control_type or "").strip().casefold()
                if kind not in {"button", "tabitem"}:
                    continue
                data = {
                    "name": str(info.name or ""),
                    "kind": kind,
                    "enabled": bool(info.enabled),
                    "visible": bool(info.visible),
                    "automation_id": str(info.automation_id or ""),
                    "runtime_id": WindowHubUIAutomationProvider._runtime_id(wrapper),
                    "wrapper": wrapper,
                }
                controls.append(data)
            except Exception:
                continue
        target = unique_start1_navigation_candidate(controls)
        if target is None:
            return False, "start1_uia_icon_not_uniquely_identified"
        import ctypes
        user32 = ctypes.windll.user32
        if not _focus_for_draft(user32, frame.handle, still_current=still_current):
            return False, "start1_main_frame_focus_refused"
        if user32.GetForegroundWindow() != frame.handle:
            return False, "start1_main_frame_focus_refused"
        # Re-read one native control identity after focus transfer.
        live_info = target["wrapper"].element_info
        if (not live_info.visible or not live_info.enabled
                or str(live_info.automation_id or "") != target["automation_id"]
                or WindowHubUIAutomationProvider._runtime_id(
                    target["wrapper"]
                ) != target["runtime_id"]):
            return False, "start1_uia_icon_changed"
        if not still_current() or user32.GetForegroundWindow() != frame.handle:
            return False, "start1_navigation_cancelled"
        if target["kind"] == "tabitem":
            target["wrapper"].iface_selection_item.Select()
        else:
            target["wrapper"].iface_invoke.Invoke()
        # Never retry this potentially non-idempotent action after dispatch.
        deadline = time.monotonic() + max(0.0, min(wait_seconds, 5.0))
        while time.monotonic() <= deadline:
            try:
                observed = adapter._capture_foreground_window()
                if (
                    (observed.active_application or "").replace(chr(92), "/")
                    .rsplit("/", 1)[-1].casefold() == "okna.exe"
                    and (observed.title or "").strip().casefold() == "okna - start1"
                ):
                    return True, "start1_native_navigation_verified"
            except Exception:
                pass
            time.sleep(0.1)
        return False, "start1_navigation_effect_uncertain_no_retry"
    except Exception as exc:
        return False, "start1_uia_navigation_unavailable_" + type(exc).__name__


def activate_windowhub_start_workspace(*, wait_seconds: float = 2.0,
                                       still_current=lambda: True) -> tuple[bool, str]:
    """Start a new draft from any screen using proven Start1 navigation.

    Prefer an existing unique Start1 window. Only if it is unavailable try
    one explicitly named UIA navigation control. Never switch documents on
    the basis of an arbitrary button or a remembered screen position.
    """
    ok, reason = activate_windowhub_wizard(
        wait_seconds=wait_seconds,
        include_workspace=True,
        prefer_start=True,
        still_current=still_current,
    )
    if ok or not still_current():
        return ok, reason
    return _activate_start1_via_unique_navigation(
        wait_seconds=wait_seconds, still_current=still_current,
    )
