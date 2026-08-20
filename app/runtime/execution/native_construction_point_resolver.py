from __future__ import annotations

import cv2
import numpy as np
import pyautogui

from app.runtime.execution.native_drawing_view_resolver import NativeDrawingViewResolver
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver


def resolve_construction_interior_point() -> tuple[int, int] | None:
    root, toolbar = NativeToolbarResolver()._find_root_and_toolbar()
    if not root:
        return None

    view = NativeDrawingViewResolver().resolve(root_hwnd=root, toolbar_hwnd=toolbar)
    if view is None:
        return None

    vx, vy, vw, vh = view["rect"]
    image = np.ascontiguousarray(np.array(pyautogui.screenshot())[:, :, ::-1])

    left, top = max(vx, 0), max(vy, 0)
    right = min(vx + vw, image.shape[1])
    bottom = min(vy + vh, image.shape[0])
    if right <= left or bottom <= top:
        return None

    crop = image[top:bottom, left:right]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    edges = cv2.Canny(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), 60, 140)

    mask = np.zeros_like(sat, dtype=np.uint8)
    mask[(sat >= 70) & (edges > 0)] = 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates: list[tuple[float, int, int, int, int]] = []
    edge_margin = 8
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if w < 60 or h < 60 or area < 4000:
            continue

        absolute_x = vx + x
        absolute_y = vy + y
        touches_view_edge = (
            absolute_x <= vx + edge_margin
            or absolute_y <= vy + edge_margin
            or absolute_x + w >= vx + vw - edge_margin
            or absolute_y + h >= vy + vh - edge_margin
        )
        if touches_view_edge:
            print(
                f"[CONSTRUCTION REJECT] drawing_view_edge rect="
                f"{(absolute_x, absolute_y, w, h)}"
            )
            continue

        roi = sat[y:y+h, x:x+w]
        edge_roi = edges[y:y+h, x:x+w]
        sat_mean = float(np.mean(roi)) / 255.0
        edge_density = float(np.count_nonzero(edge_roi)) / max(1, area)
        aspect = min(w / max(1, h), h / max(1, w))
        score = 5.0 * sat_mean + 3.0 * aspect + 4.0 * min(edge_density * 8.0, 1.0)
        candidates.append((score, x, y, w, h))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    _score, x, y, w, h = candidates[0]

    # Keep well inside the detected sash/construction, avoiding the frame border.
    inset_x = max(12, min(28, w // 8))
    inset_y = max(12, min(28, h // 8))
    px = vx + x + w // 2
    py = vy + y + h // 2 + min(20, max(8, h // 16))
    px = max(vx + x + inset_x, min(px, vx + x + w - inset_x))
    py = max(vy + y + inset_y, min(py, vy + y + h - inset_y))

    print(
        f"[CONSTRUCTION POINT] rect={(vx + x, vy + y, w, h)} "
        f"score={_score:.2f} -> interior=({px},{py})"
    )
    return int(px), int(py)
