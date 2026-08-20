from __future__ import annotations

import ctypes
from pathlib import Path

import cv2
import numpy as np

from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver, _get_window_rect
from app.runtime.execution.vision.runtime_vision import RuntimeVision

user32 = ctypes.windll.user32


def _save_overlay(image, toolbar_rect, candidates):
    overlay = image.copy()
    tx, ty, tw, th = toolbar_rect
    cv2.rectangle(overlay, (tx, ty), (tx + tw, ty + th), (255, 0, 255), 3)
    for i, (score, x, y, w, h) in enumerate(candidates[:10]):
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 255), 2)
        cv2.putText(
            overlay,
            f"{i}: {score:.2f}",
            (x, max(15, y - 4)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )
    out = Path("outputs/debug/native_drawing_region_diagnostic.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), overlay)
    print(f"[NATIVE DRAWING] Saved: {out}")


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB NATIVE DRAWING REGION DIAGNOSTIC LIVE")
    print("=" * 80)
    print("SAFE MODE: NO CLICKS")

    vision = RuntimeVision().capture()
    image = vision.screenshot.image
    if image is None or image.size == 0:
        raise RuntimeError("No screenshot available")

    resolver = NativeToolbarResolver()
    root, toolbar = resolver._find_root_and_toolbar()
    if toolbar is None:
        raise RuntimeError("Native WindowHub toolbar was not found")

    toolbar_rect = _get_window_rect(toolbar)
    print(f"[NATIVE DRAWING] root={root} toolbar={toolbar} rect={toolbar_rect}")

    h, w = image.shape[:2]
    tx, ty, tw, th = toolbar_rect

    # WindowRect exposes left/top, not x/y. Vision coordinates are relative to
    # the captured WindowHub screenshot, while the Win32 toolbar RECT is screen
    # coordinates. Convert the native toolbar to screenshot-local coordinates.
    wx, wy = vision.window.left, vision.window.top
    local_tb = (tx - wx, ty - wy, tw, th)
    lx, ly, lw, lh = local_tb
    print(f"[NATIVE DRAWING] window_origin=({wx},{wy}) local_toolbar={local_tb}")

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    sat = cv2.inRange(hsv, np.array([0, 55, 35], np.uint8), np.array([179, 255, 255], np.uint8))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 45, 140)

    # Analyze broad regions on both sides of the actual native toolbar.
    regions = []
    margin = 12
    if lx > 0:
        regions.append((0, max(0, lx - margin), 0, h))
    if lx + lw + margin < w:
        regions.append((min(w, lx + lw + margin), w, 0, h))

    candidates = []
    for rx1, rx2, ry1, ry2 in regions:
        roi_mask = sat[ry1:ry2, rx1:rx2].copy()
        roi_edges = edges[ry1:ry2, rx1:rx2]

        roi_mask = cv2.morphologyEx(roi_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
        roi_mask = cv2.morphologyEx(roi_mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), iterations=2)

        contours, _ = cv2.findContours(roi_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)
            area = cw * ch
            if area < 2000 or cw < 40 or ch < 40:
                continue
            if cw > w * 0.45 or ch > h * 0.70:
                continue
            contour_area = cv2.contourArea(contour)
            if contour_area <= 0:
                continue
            fill = contour_area / float(area)
            if fill < 0.08:
                continue

            crop_mask = roi_mask[y:y + ch, x:x + cw]
            crop_edges = roi_edges[y:y + ch, x:x + cw]
            sat_ratio = float(np.count_nonzero(crop_mask)) / float(area)
            edge_ratio = float(np.count_nonzero(crop_edges)) / float(area)
            aspect = cw / float(ch)
            shape_score = max(0.0, 1.0 - min(abs(1.0 - aspect), 1.0))

            score = sat_ratio * 6.0 + min(edge_ratio * 20.0, 4.0) + fill * 2.0 + shape_score
            candidates.append((score, rx1 + x, ry1 + y, cw, ch))

    candidates.sort(reverse=True)
    print(f"[NATIVE DRAWING] candidates={len(candidates)}")
    for i, c in enumerate(candidates[:10]):
        score, x, y, cw, ch = c
        print(f"[CANDIDATE {i:02d}] score={score:.2f} rect={x},{y} {cw}x{ch}")

    _save_overlay(image, local_tb, candidates)
    print("[PROBE] COMPLETE. No click was sent.")


if __name__ == "__main__":
    main()
