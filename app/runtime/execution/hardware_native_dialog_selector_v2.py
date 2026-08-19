from __future__ import annotations

import ctypes
import time

from app.runtime.execution.hardware_native_dialog_selector import (
    HardwareNativeDialogSelector,
)

user32 = ctypes.windll.user32


class HardwareNativeDialogSelectorV2(HardwareNativeDialogSelector):
    """Robust hardware-dialog selector.

    WindowHub has been observed to expose the hardware dialog both as a normal
    top-level popup and, depending on UI state, through an owned-window chain.
    Search both paths instead of assuming EnumWindows alone is sufficient.
    """

    TITLE_TOKEN = "Wybór okuć"
    ROOT_TITLE = "Okna -"

    def _find_dialog(self, timeout_s: float) -> int:
        deadline = time.time() + timeout_s
        last_candidates: list[tuple[int, str, str]] = []

        while time.time() < deadline:
            found = self._find_by_top_level_title()
            if found:
                print(f"[NATIVE HARDWARE V2] dialog hwnd={found}")
                return found

            root = self._find_root_by_title(self.ROOT_TITLE)
            if root:
                found = self._find_descendant_by_title(root)
                if found:
                    print(
                        f"[NATIVE HARDWARE V2] dialog found under root "
                        f"hwnd={found}"
                    )
                    return found

            last_candidates = self._window_snapshot()
            time.sleep(0.1)

        print("[NATIVE HARDWARE V2] dialog not found. Visible titled windows:")
        for hwnd, title, cls in last_candidates:
            print(f"[WINDOW] hwnd={hwnd} class={cls!r} title={title!r}")
        raise RuntimeError(
            f"Hardware dialog was not found within {timeout_s:.1f}s"
        )

    def _find_by_top_level_title(self) -> int | None:
        found: list[int] = []
        enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        @enum
        def callback(hwnd: int, _lparam: int) -> bool:
            title = self._title(hwnd)
            if self.TITLE_TOKEN.lower() in title.lower():
                found.append(int(hwnd))
                return False
            return True

        user32.EnumWindows(callback, 0)
        return found[0] if found else None

    def _find_root_by_title(self, title_token: str) -> int | None:
        found: list[int] = []
        enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        @enum
        def callback(hwnd: int, _lparam: int) -> bool:
            if title_token.lower() in self._title(hwnd).lower():
                found.append(int(hwnd))
                return False
            return True

        user32.EnumWindows(callback, 0)
        return found[0] if found else None

    def _find_descendant_by_title(self, parent: int) -> int | None:
        found: list[int] = []
        enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        @enum
        def callback(hwnd: int, _lparam: int) -> bool:
            title = self._title(hwnd)
            if self.TITLE_TOKEN.lower() in title.lower():
                found.append(int(hwnd))
                return False
            return True

        user32.EnumChildWindows(parent, callback, 0)
        return found[0] if found else None

    def _window_snapshot(self) -> list[tuple[int, str, str]]:
        result: list[tuple[int, str, str]] = []
        enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        @enum
        def callback(hwnd: int, _lparam: int) -> bool:
            if not user32.IsWindowVisible(hwnd):
                return True
            title = self._title(hwnd)
            if not title:
                return True
            cls_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buf, len(cls_buf))
            result.append((int(hwnd), title, cls_buf.value))
            return True

        user32.EnumWindows(callback, 0)
        return result

    @staticmethod
    def _title(hwnd: int) -> str:
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, len(buf))
        return buf.value.strip()
