"""Visual exact-match reader for the WindowHub customer suggestion popup.

Only scans a bounded region BELOW a freshly verified IDC_ZAMAWIAJACY
rectangle. OCR is evidence, not an authorization by itself: selection is
allowed only with one unique exact name, sufficient confidence and Win32
same-process hit-test. All matching stays in memory.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class VisualCustomerResult:
    label: str
    confidence: float
    bounds: tuple[int, int, int, int]


def popup_bounds(picker_rect: tuple[int, int, int, int],
                 screen_size: tuple[int, int]) -> tuple[int, int, int, int]:
    l, t, r, b = picker_rect
    width, height = screen_size
    if not (0 <= l < r <= width and 0 <= t < b <= height):
        raise ValueError("invalid_picker_bounds")
    # Keep the editable portion itself OUT of the image.
    return max(0, l - 45), b + 2, min(width, r + 250), min(height, b + 460)


def match_visual_customer(results: list[VisualCustomerResult],
                          name: str,
                          region: tuple[int, int, int, int]) -> list[VisualCustomerResult]:
    target = " ".join(name.casefold().split())
    x1, y1, x2, y2 = region
    return [
        result for result in results
        if " ".join(result.label.casefold().split()) == target
        and result.confidence >= 0.85
        and x1 <= result.bounds[0] < result.bounds[2] <= x2
        and y1 <= result.bounds[1] < result.bounds[3] <= y2
        and result.bounds[2] - result.bounds[0] >= 20
    ]


@lru_cache(maxsize=1)
def _ocr_engine():
    """Initialize heavyweight OCR exactly once per process, not every prefix."""
    try:
        from rapidocr_onnxruntime import RapidOCR
        return RapidOCR()
    except ImportError:
        try:
            from rapidocr import RapidOCR
            return RapidOCR()
        except ImportError:
            return None


def _ocr_text_results(image, origin):
    import numpy as np
    engine = _ocr_engine()
    if engine is None:
        return None
    try:
        output = engine(np.asarray(image))
        if isinstance(output, tuple):
            lines = output[0]
        elif hasattr(output, "boxes") and hasattr(output, "txts"):
            lines = list(zip(
                output.boxes if output.boxes is not None else [],
                output.txts if output.txts is not None else [],
                output.scores if output.scores is not None else [],
            ))
        else:
            lines = output
        if lines is None:
            return []
    except Exception:
        return None
    collected = []
    for entry in lines:
        try:
            quad, text, confidence = entry[0], entry[1], float(entry[2])
            x = [float(p[0]) for p in quad]
            y = [float(p[1]) for p in quad]
            box = (
                origin[0] + int(min(x)), origin[1] + int(min(y)),
                origin[0] + int(max(x)) + 1, origin[1] + int(max(y)) + 1,
            )
            collected.append(VisualCustomerResult(str(text).strip(), confidence, box))
        except Exception:
            continue
    return collected


def select_exact_visual_customer(scene, customer_name: str) -> tuple[bool, str]:
    from tools.run_windowhub_new_offer_native_invoke_once import resolve_native_wrapper
    from PIL import ImageGrab
    import ctypes
    from ctypes import wintypes

    hwnd = scene.observation.metadata.get("window_handle")
    if not isinstance(hwnd, int) or hwnd <= 0:
        return False, "VISUAL_CUSTOMER_NO_DOCUMENT"
    try:
        picker = resolve_native_wrapper(
            scene, label="Wybierz istniejącego klienta",
            automation_id="IDC_ZAMAWIAJACY", allowed_stages=("document_properties",),
        )
        r = picker.rectangle()
        picker_rect = (int(r.left), int(r.top), int(r.right), int(r.bottom))
    except Exception as exc:
        return False, "VISUAL_PICKER_NOT_VERIFIED_" + type(exc).__name__

    win = ctypes.WinDLL("user32", use_last_error=True)
    win.GetForegroundWindow.restype = wintypes.HWND
    if int(win.GetForegroundWindow() or 0) != hwnd:
        return False, "VISUAL_CUSTOMER_WRONG_FOREGROUND"
    win.GetSystemMetrics.argtypes = [ctypes.c_int]
    win.GetSystemMetrics.restype = ctypes.c_int
    screen = (win.GetSystemMetrics(0), win.GetSystemMetrics(1))
    try:
        region = popup_bounds(picker_rect, screen)
        if region[3] - region[1] < 40:
            return False, "VISUAL_DROPDOWN_NOT_VISIBLE"
        image = ImageGrab.grab(bbox=region, all_screens=False)
        results = _ocr_text_results(image, region)
    except Exception as exc:
        return False, "VISUAL_OCR_CAPTURE_" + type(exc).__name__
    if results is None:
        return False, "VISUAL_OCR_UNAVAILABLE"
    matches = match_visual_customer(results, customer_name, region)
    print("CUSTOMER_OCR_VISIBLE_LINE_COUNT =", len(results))
    print("CUSTOMER_OCR_EXACT_MATCHES =", len(matches))
    if len(matches) != 1:
        return False, "VISUAL_CUSTOMER_NOT_UNIQUE"

    result = matches[0]
    center = (
        (result.bounds[0] + result.bounds[2]) // 2,
        (result.bounds[1] + result.bounds[3]) // 2,
    )
    # A text OCR hit alone is NOT sufficient: ensure the exact point and
    # the verified document belong to the same process before any click.
    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]
    win.WindowFromPoint.argtypes = [POINT]
    win.WindowFromPoint.restype = wintypes.HWND
    win.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND, ctypes.POINTER(wintypes.DWORD),
    ]
    win.GetWindowThreadProcessId.restype = wintypes.DWORD
    hit = win.WindowFromPoint(POINT(*center))
    document_pid = wintypes.DWORD()
    hit_pid = wintypes.DWORD()
    win.GetWindowThreadProcessId(hwnd, ctypes.byref(document_pid))
    if not hit or not document_pid.value:
        return False, "VISUAL_CUSTOMER_HIT_UNAVAILABLE"
    win.GetWindowThreadProcessId(hit, ctypes.byref(hit_pid))
    if hit_pid.value != document_pid.value:
        return False, "VISUAL_CUSTOMER_NOT_WINDOWHUB_OWNED"
    if int(win.GetForegroundWindow() or 0) != hwnd:
        return False, "VISUAL_CUSTOMER_FOCUS_CHANGED"
    from pywinauto import mouse
    mouse.click(coords=center)
    return True, "VISUAL_EXACT_CUSTOMER_CLICKED_PENDING_VERIFICATION"
