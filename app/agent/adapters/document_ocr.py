"""Local OCR helpers for photos and image-only PDF pages.

RapidOCR is loaded lazily so ordinary text-PDF extraction and unit tests do
not need to initialize the OCR model. OCR evidence includes source-image
coordinates and engine confidence; it is never silently fabricated.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import median
from typing import Any


@dataclass(frozen=True)
class OCRTextRegion:
    """One recognized text box in coordinates of the original raster image."""

    text: str
    confidence: float | None
    x: int
    y: int
    width: int
    height: int

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2

    def to_payload(self) -> dict[str, object]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bounds": {
                "x": self.x,
                "y": self.y,
                "width": self.width,
                "height": self.height,
            },
        }


@dataclass(frozen=True)
class OCRImageResult:
    """OCR text plus bounded, spatial evidence from one image."""

    text: str
    regions: tuple[OCRTextRegion, ...]
    average_confidence: float | None


_CACHED_ENGINE: Any | None = None


def _default_engine() -> Any:
    global _CACHED_ENGINE
    if _CACHED_ENGINE is not None:
        return _CACHED_ENGINE
    try:
        from rapidocr import RapidOCR
    except ImportError as exc:
        raise RuntimeError(
            "RapidOCR is not installed; install the project requirements to read images."
        ) from exc
    _CACHED_ENGINE = RapidOCR()
    return _CACHED_ENGINE


def _regions_to_lines(regions: tuple[OCRTextRegion, ...]) -> str:
    """Build approximate reading-order text while preserving the box evidence."""
    if not regions:
        return ""

    text_sizes = [
        min(region.width, region.height)
        for region in regions
        if region.width > 0 and region.height > 0
    ]
    row_tolerance = max(8.0, median(text_sizes) * 0.7) if text_sizes else 12.0
    rows: list[list[OCRTextRegion]] = []

    for region in sorted(regions, key=lambda item: (item.center_y, item.x)):
        best_row = None
        best_distance = None
        for row in rows:
            row_center = median(item.center_y for item in row)
            distance = abs(region.center_y - row_center)
            if distance <= row_tolerance and (
                best_distance is None or distance < best_distance
            ):
                best_row = row
                best_distance = distance
        if best_row is None:
            rows.append([region])
        else:
            best_row.append(region)

    rows.sort(key=lambda row: median(item.center_y for item in row))
    lines = []
    for row in rows:
        pieces = [
            item.text.strip()
            for item in sorted(row, key=lambda item: (item.center_x, item.y))
            if item.text.strip()
        ]
        if pieces:
            lines.append(" ".join(pieces))
    return "\n".join(lines).strip()


def extract_image_text(
    image,
    *,
    engine: Any | None = None,
    min_confidence: float = 0.10,
    target_long_edge: int = 2600,
    max_upscale: float = 2.0,
) -> OCRImageResult:
    """Run RapidOCR against a PIL image and retain text-box coordinates.

    The image stays local. This function does not call a remote model, write
    files, or print recognized source text.
    """
    from PIL import Image, ImageOps
    import cv2
    import numpy as np

    if not isinstance(image, Image.Image):
        raise TypeError("extract_image_text requires a PIL Image.")
    if not 0.0 <= min_confidence <= 1.0:
        raise ValueError("min_confidence must be between 0 and 1.")
    if target_long_edge < 100 or max_upscale < 1.0:
        raise ValueError("OCR image-sizing limits are invalid.")

    oriented = ImageOps.exif_transpose(image).convert("RGB")
    original_width, original_height = oriented.size
    if original_width <= 0 or original_height <= 0:
        raise ValueError("OCR image is empty.")
    if original_width * original_height > 40_000_000:
        raise ValueError("OCR image exceeds the pixel-count safety limit.")

    scale = min(
        max_upscale,
        target_long_edge / max(original_width, original_height),
    )
    if abs(scale - 1.0) > 0.001:
        processed = oriented.resize(
            (
                max(1, int(round(original_width * scale))),
                max(1, int(round(original_height * scale))),
            ),
            Image.Resampling.LANCZOS,
        )
    else:
        processed = oriented

    rgb = np.asarray(processed)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    ocr_engine = engine if engine is not None else _default_engine()
    result = ocr_engine(bgr)

    raw_texts = getattr(result, "txts", None)
    raw_boxes = getattr(result, "boxes", None)
    raw_scores = getattr(result, "scores", None)
    if raw_texts is None or raw_boxes is None:
        return OCRImageResult("", (), None)

    scale_x = original_width / processed.width
    scale_y = original_height / processed.height
    regions: list[OCRTextRegion] = []
    for index, raw_text in enumerate(raw_texts):
        text = str(raw_text).strip() if raw_text is not None else ""
        if not text or index >= len(raw_boxes):
            continue
        try:
            points = np.asarray(raw_boxes[index], dtype=float).reshape(-1, 2)
            if len(points) < 4 or not np.isfinite(points).all():
                continue
            confidence = (
                float(raw_scores[index])
                if raw_scores is not None and index < len(raw_scores)
                else None
            )
        except (TypeError, ValueError, IndexError):
            continue
        if confidence is not None:
            if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
                continue
            if confidence < min_confidence:
                continue

        x1 = max(0, int(math.floor(float(points[:, 0].min()) * scale_x)))
        y1 = max(0, int(math.floor(float(points[:, 1].min()) * scale_y)))
        x2 = min(original_width, int(math.ceil(float(points[:, 0].max()) * scale_x)))
        y2 = min(original_height, int(math.ceil(float(points[:, 1].max()) * scale_y)))
        if x2 <= x1 or y2 <= y1:
            continue
        regions.append(
            OCRTextRegion(
                text=text,
                confidence=confidence,
                x=x1,
                y=y1,
                width=x2 - x1,
                height=y2 - y1,
            )
        )

    regions.sort(key=lambda item: (item.center_y, item.x))
    trusted_scores = [
        item.confidence for item in regions if item.confidence is not None
    ]
    average = sum(trusted_scores) / len(trusted_scores) if trusted_scores else None
    region_tuple = tuple(regions)
    return OCRImageResult(
        text=_regions_to_lines(region_tuple),
        regions=region_tuple,
        average_confidence=average,
    )


def render_pdf_page_to_image(path, page_number: int, *, dpi: int = 180):
    """Rasterize one 1-based PDF page locally for OCR."""
    from PIL import Image
    import pymupdf

    if page_number < 1:
        raise ValueError("page_number must be a positive 1-based integer.")
    if not 72 <= dpi <= 300:
        raise ValueError("PDF OCR DPI must be between 72 and 300.")

    with pymupdf.open(str(path)) as document:
        if page_number > len(document):
            raise ValueError("PDF page number is outside the document.")
        page = document[page_number - 1]
        scale = dpi / 72.0
        pixmap = page.get_pixmap(
            matrix=pymupdf.Matrix(scale, scale),
            alpha=False,
        )
        if pixmap.width * pixmap.height > 40_000_000:
            raise ValueError("Rendered PDF page exceeds the OCR pixel-count safety limit.")
        return Image.frombytes(
            "RGB",
            (pixmap.width, pixmap.height),
            pixmap.samples,
        )
