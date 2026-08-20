from __future__ import annotations

import ctypes
import ctypes.wintypes
import json
from pathlib import Path

import cv2
import numpy as np

from app.runtime.execution.native_drawing_view_resolver import NativeDrawingViewResolver
from app.runtime.execution.native_toolbar_resolver import NativeToolbarResolver


def main() -> None:
    print('=' * 80)
    print('WINDOWHUB NATIVE DRAWING VIEW CONSTRUCTION PROBE LIVE')
    print('=' * 80)
    print('SAFE MODE: NO CLICKS')

    root, toolbar = NativeToolbarResolver()._find_root_and_toolbar()
    if not root:
        raise RuntimeError('WindowHub root not found')

    view = NativeDrawingViewResolver().resolve(root_hwnd=root, toolbar_hwnd=toolbar)
    if view is None:
        raise RuntimeError('Native drawing view not resolved')

    vx, vy, vw, vh = view['rect']
    view_hwnd = view['hwnd']
    view_class = view['class']
    view_hits = view['hits']
    print(f'[DRAWING VIEW] hwnd={view_hwnd} class={view_class!r} rect={view["rect"]} hits={view_hits}')

    import pyautogui
    image = np.array(pyautogui.screenshot())[:, :, ::-1]

    left, top = max(vx, 0), max(vy, 0)
    right = min(vx + vw, image.shape[1])
    bottom = min(vy + vh, image.shape[0])
    if right <= left or bottom <= top:
        raise RuntimeError(f'Invalid drawing view crop: {view["rect"]}')

    crop = image[top:bottom, left:right]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    edges = cv2.Canny(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), 60, 140)

    mask = np.zeros_like(sat, dtype=np.uint8)
    mask[(sat >= 70) & (edges > 0)] = 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if w < 60 or h < 60 or area < 4000:
            continue
        roi = sat[y:y+h, x:x+w]
        edge_roi = edges[y:y+h, x:x+w]
        sat_mean = float(np.mean(roi)) / 255.0
        edge_density = float(np.count_nonzero(edge_roi)) / max(1, area)
        aspect = min(w / max(1, h), h / max(1, w))
        score = 5.0 * sat_mean + 3.0 * aspect + 4.0 * min(edge_density * 8.0, 1.0)
        candidates.append((score, x, y, w, h, sat_mean, edge_density))

    candidates.sort(reverse=True)
    print(f'[CONSTRUCTION] candidates={len(candidates)}')
    for score, x, y, w, h, sat_mean, edge_density in candidates[:20]:
        abs_rect = (vx + x, vy + y, w, h)
        print(f'[CANDIDATE] score={score:.2f} rect={abs_rect} sat={sat_mean:.3f} edges={edge_density:.3f}')

    if candidates:
        score, x, y, w, h, sat_mean, edge_density = candidates[0]
        center = (vx + x + w // 2, vy + y + h // 2)
        print(f'[CONSTRUCTION] FOUND rect={(vx + x, vy + y, w, h)} center={center}')
    else:
        center = None
        print('[CONSTRUCTION] NONE')

    out_dir = Path('outputs/debug')
    out_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_dir / 'native_drawing_view_construction_crop.png'), crop)
    payload = {
        'drawing_view': {
            'hwnd': view_hwnd,
            'class': view_class,
            'rect': view['rect'],
            'hits': view_hits,
        },
        'candidates': [
            {'score': s, 'rect': (vx+x, vy+y, w, h), 'sat': sat_m, 'edges': edge_d}
            for s, x, y, w, h, sat_m, edge_d in candidates
        ],
        'selected_center': center,
    }
    (out_dir / 'native_drawing_view_construction.json').write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    print(f'[NATIVE] Saved: {out_dir / "native_drawing_view_construction.json"}')
    print('[PROBE] COMPLETE. No clicks were sent.')


if __name__ == '__main__':
    main()
