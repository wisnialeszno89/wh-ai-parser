from __future__ import annotations

import cv2

from app.runtime.execution.vision.runtime_vision import RuntimeVision


def main() -> None:
    print("=" * 80)
    print("CANVAS CANDIDATE DIAGNOSTIC LIVE")
    print("=" * 80)
    print("SAFE MODE: NO CLICKS")

    vision = RuntimeVision().capture()
    screenshot = vision.screenshot
    toolbar = vision.toolbar
    if screenshot is None or toolbar is None:
        raise RuntimeError("Vision screenshot/toolbar unavailable")

    analyzer = vision  # keep runtime pipeline untouched
    image = screenshot.image.copy()
    height, width = image.shape[:2]
    top_limit = max(toolbar.bounds.bottom + 10, int(height * 0.18))
    bottom_limit = int(height * 0.92)
    roi = image[top_limit:bottom_limit]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    bright = cv2.inRange(gray, 248, 255)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    bright = cv2.morphologyEx(bright, cv2.MORPH_OPEN, kernel)
    bright = cv2.morphologyEx(bright, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if w < 60 or h < 60 or area < 5000:
            continue
        if area / float(width * height) > 0.30:
            continue
        aspect = w / float(h)
        if aspect < 0.35 or aspect > 3.0:
            continue
        contour_area = cv2.contourArea(contour)
        if contour_area <= 0:
            continue
        rectangularity = contour_area / float(area)
        if rectangularity < 0.75:
            continue
        center_y = top_limit + y + h / 2.0
        square_score = max(0.0, 1.0 - min(abs(1.0 - aspect), 1.0))
        area_ratio = area / float(width * height)
        compact_score = max(0.0, 1.0 - min(area_ratio / 0.30, 1.0))
        y_score = 1.0
        if center_y < height * 0.25:
            y_score = 0.25
        elif center_y > height * 0.78:
            y_score = 0.20
        score = rectangularity * 5.0 + square_score * 2.0 + compact_score * 2.0 + y_score * 1.5
        candidates.append((score, x, top_limit + y, w, h, rectangularity, aspect))

    candidates.sort(reverse=True)
    out = image.copy()
    for i, (score, x, y, w, h, rect, aspect) in enumerate(candidates[:15]):
        cv2.rectangle(out, (x, y), (x + w, y + h), (0, 0, 255), 2)
        label = f"#{i} score={score:.2f} {x},{y} {w}x{h}"
        cv2.putText(out, label, (x, max(15, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 255), 1, cv2.LINE_AA)
        print(f"[CANDIDATE {i:02d}] score={score:.2f} rect=({x},{y},{w},{h}) rectangularity={rect:.3f} aspect={aspect:.3f}")

    path = "outputs/debug/canvas_candidate_diagnostic.png"
    cv2.imwrite(path, out)
    print(f"[DIAGNOSTIC] Saved: {path}")
    print("[DIAGNOSTIC] NO CLICKS WERE SENT")


if __name__ == "__main__":
    main()
