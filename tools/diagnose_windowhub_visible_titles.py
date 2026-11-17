"""Read-only list of WindowHub top-level titles for local diagnostics.

No focus transfer, no clicks, no screenshots, no model calls.
Titles can include client or offer data: inspect console output before sharing.
"""
from __future__ import annotations
import ctypes
import os
from ctypes import wintypes


def run():
    if os.name != "nt":
        print("STOP=windows_required")
        return 2
    try:
        import psutil
        from app.agent.runtime.windowhub_discovery_diagnostics import categorize_window_title
        pids = {
            p.info["pid"] for p in psutil.process_iter(["pid", "name"])
            if (p.info.get("name") or "").casefold() == "okna.exe"
        }
        print("WINDOWHUB_PROCESS_COUNT=" + str(len(pids)))
        u = ctypes.WinDLL("user32", use_last_error=True)
        u.IsWindowVisible.argtypes = [wintypes.HWND]
        u.IsWindowVisible.restype = wintypes.BOOL
        u.IsIconic.argtypes = [wintypes.HWND]
        u.IsIconic.restype = wintypes.BOOL
        u.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        u.GetWindowTextLengthW.restype = ctypes.c_int
        u.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        u.GetWindowThreadProcessId.restype = wintypes.DWORD
        rows = []
        def callback(hwnd, unused):
            pid = wintypes.DWORD()
            u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value not in pids or not u.IsWindowVisible(hwnd):
                return True
            length = u.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buf = ctypes.create_unicode_buffer(length + 1)
            u.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value.strip()
            if title:
                rows.append((title, bool(u.IsIconic(hwnd))))
            return True
        cbtype = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        cb = cbtype(callback)
        u.EnumWindows.argtypes = [cbtype, wintypes.LPARAM]
        u.EnumWindows.restype = wintypes.BOOL
        u.EnumWindows(cb, 0)
        print("WINDOWHUB_VISIBLE_TITLED_COUNT=" + str(len(rows)))
        for index, (title, minimized) in enumerate(rows, start=1):
            print("WINDOW_" + str(index) + "_CATEGORY=" + categorize_window_title(title))
            print("WINDOW_" + str(index) + "_MINIMIZED=" + str(minimized))
            print("WINDOW_" + str(index) + "_TITLE=" + repr(title[:200]))
        print("WINDOWHUB_ACTIONS_EXECUTED=False")
        print("WINDOWHUB_AI_CALLS=0")
        print("PRIVACY=Titles can include business data; redact before sharing.")
        return 0
    except Exception as exc:
        print("STOP=diagnostics_unavailable_" + type(exc).__name__)
        return 4


if __name__ == "__main__":
    raise SystemExit(run())
