"""Read-only Win32 foreground PID and WindowHub ownership trace.

Does not click, raise windows, call a model, or reveal document titles.
"""
from __future__ import annotations

import ctypes
import os
import time
from ctypes import wintypes

def main():
    if os.name != "nt":
        print("WINDOWS_REQUIRED")
        return 2
    import psutil
    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = (
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD)
    )
    user32.GetAncestor.argtypes = (wintypes.HWND, wintypes.UINT)
    user32.GetAncestor.restype = wintypes.HWND
    user32.GetWindow.argtypes = (wintypes.HWND, wintypes.UINT)
    user32.GetWindow.restype = wintypes.HWND
    user32.GetClassNameW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    user32.GetClassNameW.restype = ctypes.c_int

    def owner_info(hwnd):
        if not hwnd:
            return "NONE", False, "NONE"
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        try:
            name = psutil.Process(pid.value).name().casefold()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            name = "unknown"
        if name in {"powershell.exe", "pwsh.exe", "windowsterminal.exe", "conhost.exe"}:
            category = "TERMINAL"
        elif name == "okna.exe":
            category = "WINDOWHUB"
        else:
            category = "OTHER"
        cls = ctypes.create_unicode_buffer(128)
        user32.GetClassNameW(hwnd, cls, len(cls))
        # Process executable names, unlike document titles, are useful to
        # identify browser/remote-desktop/terminal focus without personal data.
        return category + ":" + name[:64], name == "okna.exe", cls.value[:80] if category == "WINDOWHUB" else "REDACTED"

    print("=== FOREGROUND OWNERSHIP TRACE ===", flush=True)
    print("INSTRUCTION = Uzyj Alt+Tab, aby przejsc do WindowHub, potem wroc do PowerShell.", flush=True)
    print("TRACE_DURATION_SECONDS = 20", flush=True)
    print("PYTHON_PID =", os.getpid(), flush=True)
    print("IMPORTANT = Kliknij pasek tytulu WindowHub raz, zostaw na 3 sekundy, wroc do konsoli.", flush=True)
    print("TITLES_AND_DATA = HIDDEN", flush=True)
    deadline = time.monotonic() + 20.0
    previous = None
    saw_windowhub = False
    observed = 0
    while time.monotonic() < deadline:
        foreground = user32.GetForegroundWindow()
        category, direct, cls = owner_info(foreground)
        root = user32.GetAncestor(foreground, 2) if foreground else 0  # GA_ROOT
        root_cat, root_okna, _ = owner_info(root)
        owner = user32.GetWindow(foreground, 4) if foreground else 0  # GW_OWNER
        owner_cat, owner_okna, _ = owner_info(owner)
        record = (category, root_cat, owner_cat, cls)
        saw_windowhub |= direct or root_okna or owner_okna
        if record != previous:
            observed += 1
            print(
                f"CHANGE_{observed} = FOREGROUND:{category}"
                f" ROOT:{root_cat} OWNER:{owner_cat}"
                f" WINDOWHUB_CLASS:{cls}",
                flush=True,
            )
            previous = record
        time.sleep(0.1)
    print("WINDOWHUB_SEEN =", saw_windowhub)
    print("FOREGROUND_CHANGES =", observed)
    print("ACTION_TAKEN = NONE")
    print("=== TRACE END ===")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
