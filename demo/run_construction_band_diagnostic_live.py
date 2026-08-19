from __future__ import annotations

import cv2
import numpy as np

from app.runtime.execution.vision.runtime_vision import RuntimeVision


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB CONSTRUCTION BAND DIAGNOSTIC LIVE")
    print("=" * 80)
    print("SAFE MODE: NO CLICKS")
    print("Target: identify the real drawing band containing the finished window.")

    vision = RuntimeVision().capture()
    image = vision.screenshot.image
    if image is None or image.size == 0:
        raise RuntimeError("No screenshot available")

    h, w = image.shape[:2]
    # The finished construction is drawn between the upper document table and
    # the notes/editor region. Use proportional bounds for this diagnostic,
    # rather than the current CanvasAnalyzer result.
    y1 = int(h * 0.18)
    y2 = int(h * 0.40)
    x1 = 0
    x2 = int(w * 0.60)

    roi = image[y1:y2, x1:x2]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(
        hsv,
        np.array([0, 60, 35], dtype=np.uint8),
        np.array([179, 255, 255], dtype=np.uint8),
    )

    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=2)
    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)), iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for contour in contours:
        x, y, cw, ch = cv2.boundingRect(contour)
        area = cw * ch
        if area < 1500 or cw < 40 or ch < 40:
            continue
        contour_area = cv2.contourArea(contour)
        if contour_area <= 0:
            continue
        fill = contour_area / float(area)
        if fill < 0.10:
            continue
        aspect = cw / float(ch)
        if aspect < 0.35 or aspect > 2.8:
            continue
        candidate_mask = mask[y:y + ch, x:x + cw]
        sat_ratio = float(np.count_nonzero(candidate_mask)) / float(area)
        gray = cv2.cvtColor(roi[y:y + ch, x:x + cw], cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_ratio = float(np.count_nonzero(edges)) / float(area)
        score = sat_ratio * 7 + min(edge_ratio * 18, 3) + fill * 2
        candidates.append((score, x + x1, y + y1, cw, ch, sat_ratio, edge_ratio, fill))

    candidates.sort(reverse=True)
    print(f"[BAND] image={w}x{h} band=({x1},{y1})..({x2},{y2})")
    print(f"[BAND] candidates={len(candidates)}")
    for i, c in enumerate(candidates[:10]):
        score, x, y, cw, ch, sat, edge, fill = c
        print(
            f"[CANDIDATE {i:02d}] score={score:.2f} rect={x},{y} {cw}x{ch} "
            f"sat={sat:.3f} edges={edge:.3f} fill={fill:.3f}"
        )

    print("[PROBE] COMPLETE. No click was sent.")


if __name__ == "__main__":
    main()
