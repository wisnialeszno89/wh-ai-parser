from __future__ import annotations

import ctypes
import time
from dataclasses import dataclass

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# TreeView messages/constants.
TV_FIRST = 0x1100
TVM_GETNEXTITEM = TV_FIRST + 10
TVM_GETITEMW = TV_FIRST + 62
TVM_SELECTITEM = TV_FIRST + 11
TVGN_ROOT = 0x0
TVGN_NEXT = 0x1
TVGN_CHILD = 0x4

# Dialog/button messages.
BM_CLICK = 0x00F5

PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400

MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000
PAGE_READWRITE = 0x04


@dataclass(frozen=True)
class NativeTreeItem:
    handle: int
    text: str
    depth: int


class HardwareNativeDialogSelector:
    DIALOG_TITLE_PREFIX = "Wybór okuć:"
    TARGET_TEXT = "UR ACTIVPILOT"

    def select_and_confirm(self, timeout_s: float = 5.0) -> None:
        dialog = self._find_dialog(timeout_s)
        tree = self._find_child_by_class(dialog, "SysTreeView32")
        if not tree:
            raise RuntimeError("Hardware dialog TreeView was not found")

        items = self._enumerate_tree(tree)
        print(f"[NATIVE HARDWARE] tree={tree} items={len(items)}")
        for item in items:
            print(
                f"[TREE] depth={item.depth} handle={item.handle} "
                f"text={item.text!r}"
            )

        target = next(
            (item for item in items if item.text.strip() == self.TARGET_TEXT),
            None,
        )
        if target is None:
            raise RuntimeError(
                f"Hardware target {self.TARGET_TEXT!r} was not found in the TreeView"
            )

        print(
            f"[NATIVE HARDWARE] selecting {target.text!r} "
            f"handle={target.handle}"
        )
        result = user32.SendMessageW(
            tree,
            TVM_SELECTITEM,
            TVGN_CARET,
            target.handle,
        )
        if result == 0:
            raise RuntimeError("TreeView selection command failed")

        time.sleep(0.25)

        ok = user32.GetDlgItem(dialog, 1)
        if not ok:
            ok = self._find_button(dialog, "OK")
        if not ok:
            raise RuntimeError("Hardware dialog OK button was not found")

        print(f"[NATIVE HARDWARE] clicking OK hwnd={ok}")
        user32.SendMessageW(ok, BM_CLICK, 0, 0)

        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if not user32.IsWindow(dialog):
                print("[NATIVE HARDWARE] dialog closed")
                return
            time.sleep(0.1)

        raise RuntimeError("Hardware dialog did not close after OK")

    def _find_dialog(self, timeout_s: float) -> int:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            found: list[int] = []

            enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

            @enum
            def callback(hwnd: int, _lparam: int) -> bool:
                title = ctypes.create_unicode_buffer(256)
                user32.GetWindowTextW(hwnd, title, len(title))
                value = title.value.strip()
                if value.startswith(self.DIALOG_TITLE_PREFIX):
                    found.append(int(hwnd))
                    return False
                return True

            user32.EnumWindows(callback, 0)
            if found:
                print(f"[NATIVE HARDWARE] dialog hwnd={found[0]}")
                return found[0]
            time.sleep(0.1)

        raise RuntimeError(
            f"Hardware dialog was not found within {timeout_s:.1f}s"
        )

    def _find_child_by_class(self, parent: int, class_name: str) -> int | None:
        found: list[int] = []
        enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        @enum
        def callback(hwnd: int, _lparam: int) -> bool:
            cls = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls, len(cls))
            if cls.value == class_name:
                found.append(int(hwnd))
                return False
            return True

        user32.EnumChildWindows(parent, callback, 0)
        return found[0] if found else None

    def _find_button(self, parent: int, text: str) -> int | None:
        found: list[int] = []
        enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        @enum
        def callback(hwnd: int, _lparam: int) -> bool:
            cls = ctypes.create_unicode_buffer(256)
            title = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls, len(cls))
            user32.GetWindowTextW(hwnd, title, len(title))
            if cls.value == "Button" and title.value.strip() == text:
                found.append(int(hwnd))
                return False
            return True

        user32.EnumChildWindows(parent, callback, 0)
        return found[0] if found else None

    def _enumerate_tree(self, tree: int) -> list[NativeTreeItem]:
        result: list[NativeTreeItem] = []
        root = int(user32.SendMessageW(tree, TVM_GETNEXTITEM, TVGN_ROOT, 0))
        if not root:
            return result

        def walk(item: int, depth: int) -> None:
            current = item
            while current:
                text = self._get_item_text(tree, current)
                result.append(NativeTreeItem(current, text, depth))

                child = int(
                    user32.SendMessageW(
                        tree,
                        TVM_GETNEXTITEM,
                        TVGN_CHILD,
                        current,
                    )
                )
                if child:
                    walk(child, depth + 1)

                current = int(
                    user32.SendMessageW(
                        tree,
                        TVM_GETNEXTITEM,
                        TVGN_NEXT,
                        current,
                    )
                )

        walk(root, 0)
        return result

    def _get_item_text(self, tree: int, item: int) -> str:
        # WindowHub is a 32-bit process under the observed runtime, therefore
        # the native TreeView TVITEMW structure uses 32-bit pointer fields.
        # Keep this isolated so the rest of the selector remains semantic.
        pointer_size = self._remote_pointer_size(tree)
        if pointer_size != 4:
            raise RuntimeError(
                f"Unsupported TreeView target pointer size: {pointer_size}"
            )

        text_capacity = 512
        text_bytes = text_capacity * 2
        struct_size = 40
        total_size = struct_size + text_bytes

        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(tree, ctypes.byref(pid))
        process = kernel32.OpenProcess(
            PROCESS_QUERY_INFORMATION
            | PROCESS_VM_OPERATION
            | PROCESS_VM_READ
            | PROCESS_VM_WRITE,
            False,
            pid.value,
        )
        if not process:
            raise OSError("OpenProcess failed for TreeView owner")

        try:
            remote = kernel32.VirtualAllocEx(
                process,
                None,
                total_size,
                MEM_COMMIT | MEM_RESERVE,
                PAGE_READWRITE,
            )
            if not remote:
                raise OSError("VirtualAllocEx failed")

            try:
                remote_text = remote + struct_size
                tvitem = (
                    0x0001  # TVIF_TEXT
                    .to_bytes(4, "little")
                    + int(item).to_bytes(4, "little")
                    + (0).to_bytes(4, "little")
                    + (0).to_bytes(4, "little")
                    + int(remote_text).to_bytes(4, "little")
                    + int(text_capacity).to_bytes(4, "little")
                    + (0).to_bytes(4, "little")
                    + (0).to_bytes(4, "little")
                    + (0).to_bytes(4, "little")
                    + (0).to_bytes(4, "little")
                )
                written = ctypes.c_size_t()
                if not kernel32.WriteProcessMemory(
                    process,
                    ctypes.c_void_p(remote),
                    tvitem,
                    len(tvitem),
                    ctypes.byref(written),
                ):
                    raise OSError("WriteProcessMemory(TVITEMW) failed")

                result = user32.SendMessageW(
                    tree,
                    TVM_GETITEMW,
                    0,
                    remote,
                )
                if result == 0:
                    return ""

                buffer = ctypes.create_string_buffer(text_bytes)
                read = ctypes.c_size_t()
                if not kernel32.ReadProcessMemory(
                    process,
                    ctypes.c_void_p(remote_text),
                    buffer,
                    text_bytes,
                    ctypes.byref(read),
                ):
                    raise OSError("ReadProcessMemory(TreeView text) failed")

                raw = buffer.raw[: read.value]
                return raw.decode("utf-16-le", errors="ignore").split("\x00", 1)[0]
            finally:
                kernel32.VirtualFreeEx(process, ctypes.c_void_p(remote), 0, MEM_RELEASE)
        finally:
            kernel32.CloseHandle(process)

    def _remote_pointer_size(self, tree: int) -> int:
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(tree, ctypes.byref(pid))
        process = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid.value)
        if not process:
            return 4
        try:
            # The current WindowHub target is the observed 32-bit executable.
            # Keep the method explicit so this can be extended for a native
            # 64-bit build later without changing the selector API.
            return 4
        finally:
            kernel32.CloseHandle(process)
