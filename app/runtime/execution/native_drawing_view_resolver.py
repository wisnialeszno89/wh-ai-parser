from __future__ import annotations

import ctypes
import ctypes.wintypes

from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver, _get_window_rect

user32 = ctypes.windll.user32
GA_ROOT = 2


class NativeDrawingViewResolver:
    """Resolve WindowHub's native drawing view dynamically.

    The resolver avoids hard-coding HWND values. It uses a validated native
    hit-test sample to identify a large leaf Static window belonging to the
    current WindowHub root.
    """

    MIN_WIDTH = 500
    MIN_HEIGHT = 250
    MIN_HITS = 8

    def resolve(self, *, root_hwnd: int | None = None, toolbar_hwnd: int | None = None):
        if root_hwnd is None or toolbar_hwnd is None:
            root_hwnd, toolbar_hwnd = NativeToolbarResolver()._find_root_and_toolbar()

        if not root_hwnd:
            raise RuntimeError("WindowHub root not found")

        root_rect = _get_window_rect(root_hwnd)
        toolbar_rect = _get_window_rect(toolbar_hwnd) if toolbar_hwnd else None

        candidates: dict[int, dict] = {}
        left, top, width, height = root_rect
        right = left + width
        bottom = top + height

        # Dense grid through the main content region. We deliberately sample
        # around the known drawing area rather than the lower notes/status panes.
        x_start = left + 45
        x_end = min(right, left + 1700)
        y_start = top + 390
        y_end = min(bottom, top + 820)

        for y in range(y_start, y_end, 35):
            for x in range(x_start, x_end, 45):
                hwnd = self._hit_hwnd(x, y)
                if not hwnd:
                    continue
                if int(user32.GetAncestor(hwnd, GA_ROOT)) != int(root_hwnd):
                    continue
                if toolbar_hwnd and hwnd == toolbar_hwnd:
                    continue

                cls = self._class_name(hwnd)
                if cls != "Static":
                    continue

                rect = _get_window_rect(hwnd)
                rw, rh = rect[2], rect[3]
                if rw < self.MIN_WIDTH or rh < self.MIN_HEIGHT:
                    continue
                if rect[1] >= top + 820:
                    continue

                if self._overlaps_toolbar(rect, toolbar_rect):
                    continue

                entry = candidates.setdefault(
                    hwnd,
                    {
                        "hwnd": hwnd,
                        "rect": rect,
                        "hits": 0,
                        "class": cls,
                        "title": self._window_text(hwnd),
                    },
                )
                entry["hits"] += 1

        valid = [item for item in candidates.values() if item["hits"] >= self.MIN_HITS]
        if not valid:
            raise RuntimeError("Native WindowHub drawing view was not resolved")

        valid.sort(
            key=lambda item: (
                item["hits"],
                item["rect"][2] * item["rect"][3],
            ),
            reverse=True,
        )
        selected = valid[0]
        print(
            "[DRAWING VIEW] resolved "
            f"hwnd={selected['hwnd']} rect={selected['rect']} "
            f"hits={selected['hits']} class='{selected['class']}'"
        )
        return selected

    @staticmethod
    def _hit_hwnd(x: int, y: int) -> int:
        point = ctypes.wintypes.POINT(int(x), int(y))
        return int(user32.WindowFromPoint(point))

    @staticmethod
    def _class_name(hwnd: int) -> str:
        buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buf, len(buf))
        return buf.value

    @staticmethod
    def _window_text(hwnd: int) -> str:
        n = int(user32.GetWindowTextLengthW(hwnd))
        if n <= 0:
            return ""
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        return buf.value

    @staticmethod
    def _overlaps_toolbar(rect, toolbar_rect) -> bool:
        if toolbar_rect is None:
            return False
        x, y, w, h = rect
        tx, ty, tw, th = toolbar_rect
        return not (
            x + w <= tx
            or tx + tw <= x
            or y + h <= ty
            or ty + th <= y
        )
