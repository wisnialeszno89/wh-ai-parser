from __future__ import annotations

import cv2
import numpy as np

from app.runtime.execution.vision.runtime_vision import RuntimeVision


def main() -> None:
    print("=" * 80)
    print("WINDOWHUB DRAWING REGION DIAGNOSTIC LIVE")
    print("=" * 80)
    print("SAFE MODE: NO CLICKS")
    print("Target: find the actual drawing viewport from toolbar-relative geometry.")

    vision = RuntimeVision().capture()
    image = vision.screenshot.image
    toolbar = vision.toolbar
    if image is None or image.size == 0 or toolbar is None:
        raise RuntimeError("Missing screenshot or toolbar")

    h, w = image.shape[:2]
    tb = toolbar.bounds
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Strong horizontal UI separators are usually the top/bottom of the
    # drawing viewport. Search the middle document region, not the notes area.
    y0 = int(h * 0.16)
    y1 = int(h * 0.70)
    profile = np.mean(gray[y0:y1, :], axis=1)
    sharp = np.abs(np.diff(profile))
    peaks = np.where(sharp > np.percentile(sharp, 97))[0] + y0

    # Cluster nearby peak rows.
    rows: list[int] = []
    for p in peaks.tolist():
        if not rows or abs(p - rows[-1]) > 4:
            rows.append(p)

    print(f"[DRAWING] toolbar={tb.x},{tb.y} {tb.width}x{tb.height}")
    print(f"[DRAWING] horizontal separator rows={rows[:30]}")

    candidates = []
    # Evaluate pairs of separator rows. Prefer rectangles that are near the
    # toolbar horizontally and large enough to contain the finished window.
    for i, top in enumerate(rows):
        for bottom in rows[i + 1:]:
            rh = bottom - top
            if rh < 100 or rh > int(h * 0.45):
                continue

            # Both sides of the toolbar are possible; toolbar placement is user-controlled.
            spans = [
                (max(0, tb.x + tb.width + 6), w - 10),
                (10, max(10, tb.x - 6)),
            ]
            for left, right in spans:
                rw = right - left
                if rw < 200 or rw > int(w * 0.75):
                    continue

                roi = gray[top:bottom, left:right]
                if roi.size == 0:
                    continue

                # A drawing viewport is relatively light, but unlike a notes
                # editor it tends to contain dense internal structure.
                light_ratio = float(np.mean(roi > 225))
                edges = cv2.Canny(roi, 50, 150)
                edge_ratio = float(np.count_nonzero(edges)) / float(roi.size)

                center_y = (top + bottom) / 2
                center_x = (left + right) / 2
                toolbar_dx = min(abs(center_x - (tb.x + tb.width / 2)), w)

                score = (
                    light_ratio * 4.0
                    + min(edge_ratio * 20.0, 3.0)
                    + min(rw / max(w, 1), 0.5) * 2.0
                    - (0.5 if center_y > h * 0.55 else 0.0)
                )

                candidates.append((score, left, top, rw, rh, light_ratio, edge_ratio, toolbar_dx))

    candidates.sort(reverse=True)
    print(f"[DRAWING] candidates={len(candidates)}")
    for i, c in enumerate(candidates[:12]):
        score, x, y, rw, rh, light, edge, dx = c
        print(
            f"[CANDIDATE {i:02d}] score={score:.2f} rect={x},{y} {rw}x{rh} "
            f"light={light:.3f} edges={edge:.3f} toolbar_dx={dx:.0f}"
        )

    if candidates:
        _, x, y, rw, rh, *_ = candidates[0]
        vis = image.copy()
        cv2.rectangle(vis, (x, y), (x + rw, y + rh), (0, 0, 255), 3)
        path = "outputs/debug/drawing_region_diagnostic.png"
        cv2.imwrite(path, vis)
        print(f"[DRAWING] Saved: {path}")

    print("[PROBE] COMPLETE. No click was sent.")


if __name__ == "__main__":
    main()
