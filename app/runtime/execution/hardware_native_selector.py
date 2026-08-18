from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass

from app.runtime.execution.hardware_dialog_inspector import find_dialog

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000
PAGE_READWRITE = 0x04

TV_FIRST = 0x1100
TVM_GETNEXTITEM = TV_FIRST + 10
TVM_SELECTITEM = TV_FIRST + 11
TVM_GETITEMRECT = TV_FIRST + 4
TVM_GETITEMW = TV_FIRST + 62
TVGN_ROOT = 0x0000
TVGN_NEXT = 0x0001
TVGN_CHILD = 0x0004
TVIF_TEXT = 0x0001
BM_CLICK = 0x00F5


class TVITEMW_REMOTE(ctypes.Structure):
    _fields_ = [
        ("mask", wintypes.UINT),
        ("hItem", wintypes.HANDLE),
        ("state", wintypes.UINT),
        ("stateMask", wintypes.UINT),
        ("pszText", ctypes.c_void_p),
        ("cchTextMax", wintypes.INT),
        ("iImage", wintypes.INT),
        ("iSelectedImage", wintypes.INT),
        ("cChildren", wintypes.INT),
        ("lParam", ctypes.c_void_p),
    ]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


@dataclass(frozen=True)
class TreeItemInfo:
    handle: int
    text: str
    depth: int


class NativeHardwareSelector:
    """Interact with the native SysTreeView32 and OK button in WindowHub.

    SysTreeView32 belongs to the WindowHub process, not to this Python process.
    TVM_GETITEMW therefore cannot receive a Python-process pointer directly.
    We allocate the TVITEMW and text buffer inside the target process and copy
    the result back with ReadProcessMemory.
    """

    def __init__(self, dialog_hwnd: int | None = None) -> None:
        self.dialog_hwnd = int(dialog_hwnd or find_dialog() or 0)
        if not self.dialog_hwnd:
            raise RuntimeError("Hardware dialog not found")

    def find_tree(self) -> int:
        result: list[int] = []

        EnumChildProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        @EnumChildProc
        def callback(hwnd: int, _lparam: int) -> bool:
            buffer = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, buffer, len(buffer))
            if buffer.value.strip() == "SysTreeView32":
                result.append(int(hwnd))
                return False
            return True

        user32.EnumChildWindows(self.dialog_hwnd, callback, 0)
        if not result:
            raise RuntimeError("SysTreeView32 not found in hardware dialog")
        return result[0]

    @staticmethod
    def _next(tree_hwnd: int, item: int, code: int) -> int:
        return int(user32.SendMessageW(tree_hwnd, TVM_GETNEXTITEM, code, item) or 0)

    @staticmethod
    def _process_id(hwnd: int) -> int:
        pid = wintypes.DWORD()
        if not user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid)):
            raise RuntimeError(f"Unable to get process id for HWND={hwnd}")
        return int(pid.value)

    @classmethod
    def _text(cls, tree_hwnd: int, item: int) -> str:
        pid = cls._process_id(tree_hwnd)
        access = PROCESS_QUERY_INFORMATION | PROCESS_VM_OPERATION | PROCESS_VM_READ | PROCESS_VM_WRITE
        process = kernel32.OpenProcess(access, False, pid)
        if not process:
            raise RuntimeError(f"OpenProcess failed for PID={pid}")

        text_capacity = 1024
        text_bytes = text_capacity * ctypes.sizeof(ctypes.c_wchar)
        text_remote = kernel32.VirtualAllocEx(
            process,
            None,
            text_bytes,
            MEM_COMMIT | MEM_RESERVE,
            PAGE_READWRITE,
        )
        item_remote = kernel32.VirtualAllocEx(
            process,
            None,
            ctypes.sizeof(TVITEMW_REMOTE),
            MEM_COMMIT | MEM_RESERVE,
            PAGE_READWRITE,
        )

        try:
            if not text_remote or not item_remote:
                raise RuntimeError("VirtualAllocEx failed for TreeView text retrieval")

            tvitem = TVITEMW_REMOTE()
            tvitem.mask = TVIF_TEXT
            tvitem.hItem = wintypes.HANDLE(item)
            tvitem.pszText = ctypes.c_void_p(text_remote)
            tvitem.cchTextMax = text_capacity

            written = ctypes.c_size_t()
            if not kernel32.WriteProcessMemory(
                process,
                ctypes.c_void_p(item_remote),
                ctypes.byref(tvitem),
                ctypes.sizeof(tvitem),
                ctypes.byref(written),
            ):
                raise RuntimeError("WriteProcessMemory failed for TVITEMW")

            result = user32.SendMessageW(
                tree_hwnd,
                TVM_GETITEMW,
                0,
                ctypes.c_void_p(item_remote),
            )
            if not result:
                return ""

            buffer = ctypes.create_unicode_buffer(text_capacity)
            read = ctypes.c_size_t()
            if not kernel32.ReadProcessMemory(
                process,
                ctypes.c_void_p(text_remote),
                buffer,
                text_bytes,
                ctypes.byref(read),
            ):
                raise RuntimeError("ReadProcessMemory failed for TreeView text")

            return buffer.value.strip()
        finally:
            if text_remote:
                kernel32.VirtualFreeEx(process, ctypes.c_void_p(text_remote), 0, MEM_RELEASE)
            if item_remote:
                kernel32.VirtualFreeEx(process, ctypes.c_void_p(item_remote), 0, MEM_RELEASE)
            kernel32.CloseHandle(process)

    def enumerate_items(self) -> list[TreeItemInfo]:
        tree = self.find_tree()
        items: list[TreeItemInfo] = []

        def walk(item: int, depth: int) -> None:
            current = item
            while current:
                items.append(TreeItemInfo(current, self._text(tree, current), depth))
                child = self._next(tree, current, TVGN_CHILD)
                if child:
                    walk(child, depth + 1)
                current = self._next(tree, current, TVGN_NEXT)

        root = self._next(tree, 0, TVGN_ROOT)
        if root:
            walk(root, 0)
        return items

    def find_item(self, text: str) -> TreeItemInfo | None:
        wanted = " ".join(text.casefold().split())
        exact = [item for item in self.enumerate_items() if " ".join(item.text.casefold().split()) == wanted]
        return exact[0] if exact else None

    def select_item(self, item: TreeItemInfo) -> None:
        tree = self.find_tree()
        result = user32.SendMessageW(tree, TVM_SELECTITEM, TVGN_ROOT, item.handle)
        if not result:
            raise RuntimeError(f"Failed to select TreeView item: {item.text!r}")

    def click_item(self, item: TreeItemInfo) -> tuple[int, int]:
        tree = self.find_tree()
        rect = RECT()
        rect.left = item.handle
        ok = user32.SendMessageW(tree, TVM_GETITEMRECT, 1, ctypes.byref(rect))
        if not ok:
            raise RuntimeError(f"Unable to get rectangle for TreeView item: {item.text!r}")

        point = wintypes.POINT((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2)
        if not user32.ClientToScreen(tree, ctypes.byref(point)):
            raise RuntimeError("ClientToScreen failed for TreeView item")

        user32.SetCursorPos(point.x, point.y)
        user32.mouse_event(0x0002, 0, 0, 0, 0)
        user32.mouse_event(0x0004, 0, 0, 0, 0)
        return point.x, point.y

    def find_ok(self) -> int:
        result: list[int] = []
        EnumChildProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        @EnumChildProc
        def callback(hwnd: int, _lparam: int) -> bool:
            buffer = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, buffer, len(buffer))
            if buffer.value.strip() != "Button":
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            text = ctypes.create_unicode_buffer(max(length + 1, 64))
            user32.GetWindowTextW(hwnd, text, len(text))
            if text.value.strip().casefold() == "ok" and user32.IsWindowVisible(hwnd):
                result.append(int(hwnd))
                return False
            return True

        user32.EnumChildWindows(self.dialog_hwnd, callback, 0)
        if not result:
            raise RuntimeError("OK button not found in hardware dialog")
        return result[0]

    def click_ok(self) -> int:
        hwnd = self.find_ok()
        result = user32.SendMessageW(hwnd, BM_CLICK, 0, 0)
        if not result:
            user32.PostMessageW(hwnd, BM_CLICK, 0, 0)
        return hwnd
