"""Read-only Win32 window-title diagnosis for Okna.exe, no third-party packages.

No focus change, clicks, screenshots, model calls or document mutation.
Window titles can contain customer data: redact before sharing.
"""
from __future__ import annotations
import ctypes
import os
from ctypes import wintypes


def run() -> int:
    if os.name != "nt":
        print("STOP=windows_required")
        return 2
    try:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        TH32CS_SNAPPROCESS = 0x00000002
        INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

        class PROCESSENTRY32W(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", wintypes.WCHAR * 260),
            ]

        kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        kernel32.Process32FirstW.restype = wintypes.BOOL
        kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        kernel32.Process32NextW.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot in (None, 0, INVALID_HANDLE_VALUE):
            print("STOP=process_snapshot_failed")
            return 4
        pids = set()
        try:
            item = PROCESSENTRY32W()
            item.dwSize = ctypes.sizeof(item)
            found = kernel32.Process32FirstW(snapshot, ctypes.byref(item))
            while found:
                if item.szExeFile.casefold() == "okna.exe":
                    pids.add(int(item.th32ProcessID))
                found = kernel32.Process32NextW(snapshot, ctypes.byref(item))
        finally:
            kernel32.CloseHandle(snapshot)

        print("WINDOWHUB_PROCESS_COUNT=" + str(len(pids)))
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
        user32.EnumWindows.restype = wintypes.BOOL
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.IsIconic.argtypes = [wintypes.HWND]
        user32.IsIconic.restype = wintypes.BOOL
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = ctypes.c_int
        user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND, ctypes.POINTER(wintypes.DWORD)
        ]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD

        rows = []
        def inspect(hwnd, ignored):
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if int(pid.value) not in pids or not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            title_buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title_buffer, length + 1)
            title = title_buffer.value.strip()
            if title:
                rows.append((title, bool(user32.IsIconic(hwnd))))
            return True

        callback = callback_type(inspect)
        user32.EnumWindows(callback, 0)
        print("WINDOWHUB_VISIBLE_TITLED_COUNT=" + str(len(rows)))
        # Local diagnosis only; never logged to a remote model.
        for index, (title, minimized) in enumerate(rows, 1):
            normalized = title.casefold()
            category = (
                "wizard" if normalized in {
                    "dodawanie nowej pozycji", "wielkość okna",
                    "podstawowe parametry okna", "parametry szklenia",
                    "parametry parapetu", "parametry okuć",
                } else "dialog" if normalized in {
                    "właściwości dokumentu", "zakładanie nowego klienta"
                } else "start" if normalized.startswith("okna - start1")
                else "document" if normalized.startswith("okna - ofr/")
                else "unrecognized"
            )
            print(f"WINDOW_{index}_CATEGORY={category}")
            print(f"WINDOW_{index}_MINIMIZED={minimized}")
            print(f"WINDOW_{index}_TITLE={title[:200]!r}")
        print("WINDOWHUB_ACTIONS_EXECUTED=False")
        print("WINDOWHUB_AI_CALLS=0")
        print("PRIVACY=Redact business details from titles before sharing.")
        return 0
    except Exception as exc:
        print("STOP=diagnostics_unavailable_" + type(exc).__name__)
        return 4


if __name__ == "__main__":
    raise SystemExit(run())
