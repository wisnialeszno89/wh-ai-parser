"""Diagnose WindowHub discovery without activating unknown windows.

Only counts processes and top-level window categories. No document titles,
customer names, native window IDs or screen content are logged.
"""
from __future__ import annotations


def categorize_window_title(title: str) -> str:
    normalized = (title or "").strip().casefold()
    if normalized in {
        "dodawanie nowej pozycji", "wielkość okna",
        "podstawowe parametry okna", "parametry szklenia",
        "parametry parapetu", "parametry okuć",
    }:
        return "wizard"
    if normalized in {"właściwości dokumentu", "zakładanie nowego klienta"}:
        return "dialog"
    if normalized.startswith("okna - start1"):
        return "start"
    if normalized.startswith("okna - ofr/"):
        return "document"
    if normalized.startswith("okna - zlc/"):
        return "order_document"
    return "unrecognized"


def diagnostic_counts() -> dict[str, int]:
    import os
    if os.name != "nt":
        return {"windows_required": 1}
    import ctypes
    from ctypes import wintypes
    import psutil
    counts = {k: 0 for k in (
        "processes", "visible_titled_windows", "wizard", "dialog",
        "start", "document", "order_document", "unrecognized",
    )}
    active_pids = set()
    for process in psutil.process_iter(["pid", "name"]):
        try:
            if (process.info.get("name") or "").casefold() == "okna.exe":
                active_pids.add(process.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    counts["processes"] = len(active_pids)
    if not active_pids:
        return counts

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
    )
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD

    def inspect(hwnd, param):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if int(pid.value) not in active_pids:
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        counts["visible_titled_windows"] += 1
        counts[categorize_window_title(buffer.value)] += 1
        return True

    callback = callback_type(inspect)
    user32.EnumWindows(callback, 0)
    return counts


def suggest_recovery(counts: dict[str, int]) -> str:
    if counts.get("windows_required"):
        return "windows_required"
    if counts.get("processes", 0) == 0:
        return "windowhub_process_not_running"
    if counts.get("visible_titled_windows", 0) == 0:
        return "no_visible_titled_window_or_application_minimized_to_tray"
    if counts.get("unrecognized", 0) > 0 and not any(
        counts.get(item, 0) for item in ("wizard", "dialog", "start", "document", "order_document")
    ):
        return "windowhub_running_but_title_not_mapped"
    if sum(counts.get(item, 0) for item in ("wizard", "dialog", "start", "document", "order_document")) > 1:
        return "multiple_workflow_windows_need_context"
    if sum(counts.get(item, 0) for item in ("wizard", "dialog", "start", "document", "order_document")) == 1:
        return "known_window_exists_focus_or_permission_issue"
    return "environment_unresolved"


def print_discovery_diagnostics():
    counts = diagnostic_counts()
    print("WINDOWHUB_DISCOVERY_DIAGNOSTIC=" + suggest_recovery(counts))
    for key, value in counts.items():
        print("WINDOWHUB_WINDOW_COUNT_" + key.upper() + "=" + str(value))
    print("NO_UNKNOWN_WINDOW_ACTIVATION=True")


if __name__ == "__main__":
    print_discovery_diagnostics()
