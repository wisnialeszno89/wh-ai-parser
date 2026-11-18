"""Read tooltip text from visual changes after a hover.

Works without UI Automation. Uses a single targeted OCR call per hover, only
on a bounded changed region, and returns evidence rather than click authority.
No action is performed by this module.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageOps


def changed_regions(before: Image.Image, after: Image.Image, pointer: tuple[int, int]):
    """Return potential tooltip rectangles, excluding the immediate pointer."""
    import cv2

    a = np.asarray(before.convert("RGB"), dtype=np.int16)
    b = np.asarray(after.convert("RGB"), dtype=np.int16)
    if a.shape != b or a.ndim != 3:
        return []
    mask = (np.max(np.abs(a - b), axis=2) >= 25).astype(np.uint8)
    x, y = pointer
    h, w = mask.shape
    mask[max(0, y - 12):min(h, y + 16),
         max(0, x - 12):min(w, x + 16)] = 0
    # Connect changed letters and a tooltip background within a block.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (19, 9))
    joined = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(joined, 8)
    candidates = []
    for idx in range(1, n):
        left, top, width, height, area = map(int, stats[idx])
        if not (120 <= area and 18 <= width <= min(850, w)
                and 13 <= height <= min(260, h)):
            continue
        if width * height > int(w * h * .20):
            continue
        # Tooltip may appear below/right or above the hovered control.
        px, py = pointer
        dist = max(0, left - px, px - (left + width)) + max(
            0, top - py, py - (top + height)
        )
        if dist > 650:
            continue
        pad = 5
        candidates.append((
            (dist, -(width * height)),
            [max(0, left - pad), max(0, top - pad),
             min(w, left + width + pad), min(h, top + height + pad)],
        ))
    candidates.sort(key=lambda row: row[0])
    return [rect for _, rect in candidates[:4]]


def tooltip_ocr(
    before: Image.Image | None,
    after: Image.Image | None,
    pointer: tuple[int, int],
    *,
    crops_folder: Path | None = None,
    step: int = 0,
    lang: str = "eng",
) -> dict:
    """OCR only changed tooltip candidates. Absence stays unverified.

    A text candidate is not a validated icon function until a later test
    checks the UI behavior. Never interpret OCR as authorization to click.
    """
    result = {"status": "no_visual_change", "text": None,
              "confidence": None, "bounds": None, "candidates": 0}
    if before is None or after is None:
        return result
    regions = changed_regions(before, after, pointer)
    result["candidates"] = len(regions)
    if not regions:
        return result
    try:
        import pytesseract
    except ImportError:
        result["status"] = "pytesseract_missing"
        return result
    best = None
    for idx, bounds in enumerate(regions):
        crop = after.crop(tuple(bounds))
        if crops_folder is not None:
            crops_folder.mkdir(parents=True, exist_ok=True)
            crop.save(crops_folder / f"tooltip_{step:02d}_{idx}.png")
        try:
            enhanced = ImageEnhance.Contrast(
                ImageOps.grayscale(crop).resize(
                    (crop.width * 3, crop.height * 3)
                )
            ).enhance(1.8)
            data = pytesseract.image_to_data(
                enhanced, lang=lang, config="--psm 6",
                output_type=pytesseract.Output.DICT,
                timeout=7,
            )
        except pytesseract.TesseractNotFoundError:
            result["status"] = "tesseract_binary_missing"
            return result
        except (RuntimeError, OSError, ValueError) as exc:
            result["status"] = "ocr_error_" + type(exc).__name__
            continue
        words = []
        confidences = []
        for word, conf in zip(data.get("text", []), data.get("conf", [])):
            word = str(word).strip()
            try:
                confidence = float(conf)
            except (TypeError, ValueError):
                continue
            if word and confidence >= 35:
                words.append(word)
                confidences.append(confidence)
        text = " ".join(words).strip()[:220]
        if len(text) < 3:
            continue
        confidence = round(sum(confidences) / len(confidences), 1)
        if best is None or confidence > best[0]:
            best = (confidence, text, bounds)
    if best is not None:
        result.update(status="ocr_candidate_unverified",
                      confidence=best[0], text=best[1], bounds=best[2])
    elif result["status"] == "no_visual_change":
        result["status"] = "visual_change_no_readable_text"
    return result
