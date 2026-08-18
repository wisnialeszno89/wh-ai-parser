from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass

from app.runtime.execution.hardware_dialog_inspector import find_dialog

user32 = ctypes.windll.user32

TV_FIRST = 0x1100
TVM_GETNEXTITEM = TV_FIRST + 10
TVM_SELECTITEM = TV_FIRST + 11
TVM_GETITEMRECT = TV_FIRST + 4
TVM_GETITEMW = TV_FIRST + 62
TVGN_ROOT = 0x0000
TVGN_NEXT = 0x0001
TVGN_CHILD = 0x0004
TVIF_TEXT = 0x0001
TV_FIRST = 0x1100
BM_CLICK = 0x00F5


class TVITEMW(ctypes.Structure):
    _fields_ = [
        ("mask", wintypes.UINT),
        ("hItem", wintypes.HANDLE),
        ("state", wintypes.UINT),
        ("stateMask", wintypes.UINT),
        ("pszText", wintypes.LPWSTR),
        ("cchTextMax", wintypes.INT),
        ("iImage", wintypes.INT),
        ("iSelectedImage", wintypes.INT),
        ("cChildren", wintypes.INT),
        ("lParam", wintypes.LPARAM),
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
    """Interact with the native SysTreeView32 and OK button in WindowHub."""

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
    def _text(tree_hwnd: int, item: int) -> str:
        buffer = ctypes.create_unicode_buffer(512)
        tvitem = TVITEMW()
        tvitem.mask = TVIF_TEXT
        tvitem.hItem = wintypes.HANDLE(item)
        tvitem.pszText = ctypes.cast(buffer, wintypes.LPWSTR)
        tvitem.cchTextMax = len(buffer)
        ok = user32.SendMessageW(tree_hwnd, TVM_GETITEMW, 0, ctypes.byref(tvitem))
        if not ok:
            return ""
        return buffer.value.strip()

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
        if exact:
            return exact[0]
        return None

    def select_item(self, item: TreeItemInfo) -> None:
        tree = self.find_tree()
        result = user32.SendMessageW(
            tree,
            TVM_SELECTITEM,
            TVGN_ROOT,
            item.handle,
        )
        if not result:
            raise RuntimeError(f"Failed to select TreeView item: {item.text!r}")

    def click_item(self, item: TreeItemInfo) -> tuple[int, int]:
        tree = self.find_tree()
        rect = RECT()
        # TVM_GETITEMRECT expects the item handle in RECT.left when wParam=True.
        rect.left = item.handle
        ok = user32.SendMessageW(tree, TVM_GETITEMRECT, 1, ctypes.byref(rect))
        if not ok:
            raise RuntimeError(f"Unable to get rectangle for TreeView item: {item.text!r}")

        point = wintypes.POINT(
            (rect.left + rect.right) // 2,
            (rect.top + rect.bottom) // 2,
        )
        if not user32.ClientToScreen(tree, ctypes.byref(point)):
            raise RuntimeError("ClientToScreen failed for TreeView item")

        # Real mouse click is the closest analogue to the user's manual action.
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
            # Some older controls return zero even when BM_CLICK was handled.
            user32.PostMessageW(hwnd, BM_CLICK, 0, 0)
        return hwnd
