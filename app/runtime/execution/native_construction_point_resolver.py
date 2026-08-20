from __future__ import annotations

import cv2
import numpy as np
import pyautogui

from app.runtime.execution.native_drawing_view_resolver import NativeDrawingViewResolver
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver


def _candidate_touches_view_edge(vx: int, vy: int, vw: int, vh: int, x: int, y: int, w: int, h: int) -> bool:
    right = x + w
    bottom = y + h
    view_right = vx + vw
    view_bottom = vy + vh
    tol = 3
    return (
        x <= vx + tol
        or y <= vy + tol
        or right >= view_right - tol
        or bottom >= view_bottom - tol
    )


def _pick_candidate(
    candidates: list[tuple[float, int, int, int, int]],
) -> tuple[float, int, int, int, int] | None:
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0]


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
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 60, 140)

    # Primary mask: keep saturated pixels that also have visible structure.
    mask = np.zeros_like(sat, dtype=np.uint8)
    mask[(sat >= 70) & (edges > 0)] = 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates: list[tuple[float, int, int, int, int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if w < 60 or h < 60 or area < 4000:
            continue
        sx, sy = vx + x, vy + y
        if _candidate_touches_view_edge(vx, vy, vw, vh, sx, sy, w, h):
            print(f"[CONSTRUCTION REJECT] drawing_view_edge rect=({sx}, {sy}, {w}, {h})")
            continue
        roi = sat[y:y+h, x:x+w]
        edge_roi = edges[y:y+h, x:x+w]
        sat_mean = float(np.mean(roi)) / 255.0
        edge_density = float(np.count_nonzero(edge_roi)) / max(1, area)
        aspect = min(w / max(1, h), h / max(1, w))
        area_score = min(area / 160000.0, 1.0)
        center_x = sx + w / 2.0
        center_y = sy + h / 2.0
        center_margin = min(
            center_x - vx,
            (vx + vw) - center_x,
            center_y - vy,
            (vy + vh) - center_y,
        ) / max(1.0, min(vw, vh))
        score = (
            5.0 * sat_mean
            + 3.0 * aspect
            + 4.0 * min(edge_density * 8.0, 1.0)
            + 2.0 * area_score
            + 2.0 * max(center_margin, 0.0)
        )
        candidates.append((score, x, y, w, h))

    selected = _pick_candidate(candidates)

    # Fallback: some real WindowHub constructions have weak/fragmented edges.
    # Use saturation alone and the same geometric edge rejection.
    if selected is None:
        fallback = np.zeros_like(sat, dtype=np.uint8)
        fallback[sat >= 55] = 255
        fallback = cv2.morphologyEx(fallback, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8), iterations=2)
        fallback = cv2.morphologyEx(fallback, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8), iterations=1)
        fallback_contours, _ = cv2.findContours(fallback, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        fallback_candidates: list[tuple[float, int, int, int, int]] = []
        for contour in fallback_contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            if w < 120 or h < 120 or area < 12000:
                continue
            sx, sy = vx + x, vy + y
            if _candidate_touches_view_edge(vx, vy, vw, vh, sx, sy, w, h):
                print(f"[CONSTRUCTION REJECT] fallback drawing_view_edge rect=({sx}, {sy}, {w}, {h})")
                continue
            aspect = min(w / max(1, h), h / max(1, w))
            sat_mean = float(np.mean(sat[y:y+h, x:x+w])) / 255.0
            center_x = sx + w / 2.0
            center_y = sy + h / 2.0
            center_margin = min(
                center_x - vx,
                (vx + vw) - center_x,
                center_y - vy,
                (vy + vh) - center_y,
            ) / max(1.0, min(vw, vh))
            score = 7.0 * aspect + 5.0 * min(area / 180000.0, 1.0) + 2.0 * sat_mean + 3.0 * max(center_margin, 0.0)
            fallback_candidates.append((score, x, y, w, h))
        selected = _pick_candidate(fallback_candidates)
        if selected is not None:
            score, x, y, w, h = selected
            print(f"[CONSTRUCTION FALLBACK] rect=({vx+x}, {vy+y}, {w}, {h}) score={score:.2f}")

    if selected is None:
        return None

    score, x, y, w, h = selected
    inset_x = max(12, min(28, w // 8))
    inset_y = max(12, min(28, h // 8))
    px = vx + x + w // 2
    py = vy + y + h // 2 + min(20, max(8, h // 16))
    px = max(vx + x + inset_x, min(px, vx + x + w - inset_x))
    py = max(vy + y + inset_y, min(py, vy + y + h - inset_y))

    print(
        f"[CONSTRUCTION POINT] rect={(vx + x, vy + y, w, h)} "
        f"score={score:.2f} -> interior=({px},{py})"
    )
    return int(px), int(py)
