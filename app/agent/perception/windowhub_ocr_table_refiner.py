"""Conservative local OCR recovery for incomplete WindowHub table rows."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace
from typing import Any, Callable, Iterable

import cv2
import numpy as np

from app.agent.perception.windowhub_ocr_table_parser import WindowHubOCRTableRow


@dataclass(frozen=True)
class WindowHubOCRFieldRefinement:
    row_index: int
    field: str
    previous_value: str | int | None
    candidate_value: str | int | None
    accepted: bool
    confidence: float
    sources: tuple[str, ...]
    reason: str

    def to_payload(self) -> dict[str, object]:
        return {
            "row_index": self.row_index,
            "field": self.field,
            "previous_value": self.previous_value,
            "candidate_value": self.candidate_value,
            "accepted": self.accepted,
            "confidence": self.confidence,
            "sources": list(self.sources),
            "reason": self.reason,
        }


def _normalize_article(value: str) -> str:
    return "".join(char for char in value.casefold() if char.isalnum())


def _parse_money(text: str) -> str | None:
    value = re.sub(r"\s+", "", text)
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+,\d{2}", value):
        value = value.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d+,\d{2}", value):
        value = value.replace(",", ".")
    elif not re.fullmatch(r"\d+\.\d{2}", value):
        return None
    return value


def _result_items(result: Any) -> list[tuple[str, float]]:
    if result is None:
        return []
    texts = getattr(result, "txts", None)
    scores = getattr(result, "scores", None)
    if texts is None:
        return []
    output: list[tuple[str, float]] = []
    for index, text in enumerate(texts):
        if text is None:
            continue
        try:
            confidence = float(scores[index]) if scores is not None and index < len(scores) else 0.0
        except (TypeError, ValueError, IndexError):
            confidence = 0.0
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            continue
        output.append((str(text).strip(), confidence))
    return output


def _read_variants(
    engine: Callable[[np.ndarray], Any],
    crop: np.ndarray,
    *,
    scale: int,
) -> tuple[tuple[str, list[tuple[str, float]]], ...]:
    if crop.size == 0:
        return ()
    enlarged = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return (
        ("color", _result_items(engine(enlarged))),
        ("otsu", _result_items(engine(otsu))),
    )


def _read_dimension_variants(
    engine: Callable[[np.ndarray], Any],
    crop: np.ndarray,
    *,
    scale: int = 6,
) -> tuple[tuple[str, list[tuple[str, float]]], ...]:
    """Read a wider, padded dimension-cell crop with contrast-aware variants.

    WindowHub's dimension strings can be clipped when the crop starts at x=1000.
    Use a leftward-bounded crop, enlargement, added whitespace, CLAHE/sharpening,
    and Otsu thresholding to preserve the first digit and multiplication mark.
    """
    if crop.size == 0:
        return ()
    enlarged = cv2.resize(
        crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
    )
    gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(
        clipLimit=2.0, tileGridSize=(8, 8)
    ).apply(gray)
    sharpened = cv2.addWeighted(
        clahe,
        1.6,
        cv2.GaussianBlur(clahe, (0, 0), 1.0),
        -0.6,
        0,
    )
    _, otsu = cv2.threshold(
        sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    border_x, border_y = 48, 20
    variants = (
        (
            "color",
            cv2.copyMakeBorder(
                enlarged, border_y, border_y, border_x, border_x,
                cv2.BORDER_CONSTANT, value=(255, 255, 255),
            ),
        ),
        (
            "clahe_sharpened",
            cv2.copyMakeBorder(
                sharpened, border_y, border_y, border_x, border_x,
                cv2.BORDER_CONSTANT, value=255,
            ),
        ),
        (
            "otsu_sharpened",
            cv2.copyMakeBorder(
                otsu, border_y, border_y, border_x, border_x,
                cv2.BORDER_CONSTANT, value=255,
            ),
        ),
    )
    return tuple(
        (source, _result_items(engine(variant_image)))
        for source, variant_image in variants
    )


def _quantity_candidates(
    variants: Iterable[tuple[str, list[tuple[str, float]]]],
    expected_article: str,
    *,
    min_confidence: float,
) -> list[tuple[int, float, str]]:
    expected = _normalize_article(expected_article)
    candidates: list[tuple[int, float, str]] = []
    standalone_quantities: list[tuple[int, float, str]] = []
    matching_articles: list[tuple[float, str]] = []
    if not expected:
        return candidates

    for source, items in variants:
        for text, confidence in items:
            if confidence < min_confidence:
                continue
            match = re.fullmatch(r"(\d{1,2})\s*(.*?)", text)
            if match:
                quantity = int(match.group(1))
                article = match.group(2).strip()
                if quantity > 0 and _normalize_article(article) == expected:
                    candidates.append((quantity, confidence, source))
                elif not article and quantity > 0:
                    standalone_quantities.append((quantity, confidence, source))
            if _normalize_article(text) == expected:
                matching_articles.append((confidence, source))

    # Both preprocessing variants are run on the same row-bounded crop.
    # A digit found in one variant can therefore be corroborated by the
    # expected article found in the other variant; requiring both tokens to
    # appear in the same OCR output needlessly loses valid quantity evidence.
    for quantity, quantity_confidence, quantity_source in standalone_quantities:
        for article_confidence, article_source in matching_articles:
            source = (
                quantity_source
                if quantity_source == article_source
                else f"{quantity_source}+{article_source}"
            )
            candidates.append(
                (quantity, min(quantity_confidence, article_confidence), source)
            )
    return candidates



def _parse_dimensions_candidate(text: str) -> str | None:
    """Parse only explicit width-by-height OCR text; do not infer values."""
    value = re.sub(r"\s+", "", text)
    match = re.search(r"(?<!\d)(\d{2,4})[xX×Îî](\d{2,4})(?!\d)", value)
    return f"{match.group(1)} x {match.group(2)}" if match else None

def _dimension_candidates(variants, *, min_confidence: float):
    candidates = []
    for source, items in variants:
        for text, confidence in items:
            if confidence < min_confidence:
                continue
            value = _parse_dimensions_candidate(text)
            if value is not None:
                candidates.append((value, confidence, source))
    return candidates
def _money_candidates(
    variants: Iterable[tuple[str, list[tuple[str, float]]]],
    *,
    min_confidence: float,
) -> list[tuple[str, float, str]]:
    candidates: list[tuple[str, float, str]] = []
    for source, items in variants:
        for text, confidence in items:
            if confidence < min_confidence:
                continue
            value = _parse_money(text)
            if value is not None:
                candidates.append((value, confidence, source))
    return candidates


def _resolve_candidates(
    candidates: list[tuple[Any, float, str]],
) -> tuple[Any | None, float, tuple[str, ...], str]:
    if not candidates:
        return None, 0.0, (), "no_valid_candidate"
    distinct_values = {candidate[0] for candidate in candidates}
    sources = tuple(sorted({candidate[2] for candidate in candidates}))
    confidence = max(candidate[1] for candidate in candidates)
    if len(distinct_values) != 1:
        return None, confidence, sources, "conflicting_candidates"
    return next(iter(distinct_values)), confidence, sources, "unique_valid_candidate"


def _normalize_image(screenshot_or_image: Any) -> np.ndarray:
    image = getattr(screenshot_or_image, "image", screenshot_or_image)
    image = np.asarray(image)
    if image.size == 0 or image.ndim not in (2, 3):
        raise ValueError("Screenshot image is empty or has an invalid shape")
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    if image.shape[2] != 3:
        raise ValueError("Screenshot must have 1, 3 or 4 channels")
    return image


def _row_crop_bounds(
    rows: tuple[WindowHubOCRTableRow, ...],
    row: WindowHubOCRTableRow,
    *,
    image_height: int,
    row_half_height: int,
) -> tuple[int, int]:
    """Return a vertical row band bounded by midpoints to adjacent table rows.

    A fixed crop centered on the price can clip quantity/article text when OCR
    boxes for different columns have different vertical centers. Expanding to
    the neighbouring-row midpoints captures the whole row without including
    the next row's center. Outer rows use their nearest row gap as a guide.
    """
    center = float(row.center_y)
    centers = sorted({
        float(other.center_y)
        for other in rows
        if float(other.center_y) != center
    })
    previous = max((value for value in centers if value < center), default=None)
    following = min((value for value in centers if value > center), default=None)

    if previous is not None:
        y0 = math.floor((previous + center) / 2)
    else:
        outer_gap = (following - center) / 2 if following is not None else 0
        y0 = math.floor(center - max(row_half_height, outer_gap))

    if following is not None:
        y1 = math.ceil((center + following) / 2)
    else:
        outer_gap = (center - previous) / 2 if previous is not None else 0
        y1 = math.ceil(center + max(row_half_height, outer_gap))

    if image_height <= 0:
        return 0, 0
    y0 = max(0, min(image_height - 1, y0))
    y1 = max(y0 + 1, min(image_height, y1))
    return y0, y1


def refine_windowhub_ocr_table_rows(
    rows: Iterable[WindowHubOCRTableRow],
    screenshot_or_image: Any,
    engine: Callable[[np.ndarray], Any],
    *,
    min_confidence: float = 0.85,
    money_min_confidence: float = 0.90,
    row_half_height: int = 9,
    scale: int = 4,
    article_x_min: int = 190,
    article_x_max: int = 380,
    unit_x_min: int = 510,
    unit_x_max: int = 600,
    dimensions_x_min: int = 850,
    dimensions_x_max: int = 1350,
    dimensions_min_confidence: float = 0.85,
) -> tuple[tuple[WindowHubOCRTableRow, ...], tuple[WindowHubOCRFieldRefinement, ...]]:
    """Recover missing quantity/unit-price/dimension fields without guessing."""
    input_rows = tuple(rows)
    if not input_rows or all(row.quantity is not None and row.unit_value is not None and row.dimensions is not None for row in input_rows):
        return input_rows, ()
    image = _normalize_image(screenshot_or_image)
    height, width = image.shape[:2]
    refined_rows: list[WindowHubOCRTableRow] = []
    reports: list[WindowHubOCRFieldRefinement] = []

    for row in input_rows:
        quantity = row.quantity
        unit_value = row.unit_value
        dimensions = row.dimensions
        y0, y1 = _row_crop_bounds(
            input_rows,
            row,
            image_height=height,
            row_half_height=row_half_height,
        )
        if quantity is None and row.article:
            x0 = max(0, article_x_min)
            x1 = min(width, article_x_max)
            variants = _read_variants(engine, image[y0:y1, x0:x1], scale=scale)
            candidates = _quantity_candidates(variants, row.article, min_confidence=min_confidence)
            value, confidence, sources, reason = _resolve_candidates(candidates)
            accepted = value is not None
            if accepted:
                quantity = int(value)
            reports.append(WindowHubOCRFieldRefinement(
                row_index=row.row_index, field="quantity", previous_value=row.quantity,
                candidate_value=value, accepted=accepted, confidence=confidence,
                sources=sources, reason=reason,
            ))
        if unit_value is None:
            x0 = max(0, unit_x_min)
            x1 = min(width, unit_x_max)
            variants = _read_variants(engine, image[y0:y1, x0:x1], scale=scale)
            candidates = _money_candidates(variants, min_confidence=money_min_confidence)
            value, confidence, sources, reason = _resolve_candidates(candidates)
            accepted = value is not None
            if accepted:
                unit_value = str(value)
            reports.append(WindowHubOCRFieldRefinement(
                row_index=row.row_index, field="unit_value", previous_value=row.unit_value,
                candidate_value=value, accepted=accepted, confidence=confidence,
                sources=sources, reason=reason,
            ))
        if dimensions is None:
            x0 = max(0, dimensions_x_min)
            x1 = min(width, dimensions_x_max)
            variants = _read_dimension_variants(
                engine, image[y0:y1, x0:x1], scale=6
            )
            candidates = _dimension_candidates(
                variants, min_confidence=dimensions_min_confidence
            )
            value, confidence, sources, reason = _resolve_candidates(candidates)
            accepted = value is not None
            if accepted:
                dimensions = str(value)
            reports.append(WindowHubOCRFieldRefinement(
                row_index=row.row_index, field="dimensions", previous_value=row.dimensions,
                candidate_value=value, accepted=accepted, confidence=confidence,
                sources=sources, reason=reason,
            ))
        fields = {
            "lp": row.lp, "quantity": quantity, "article": row.article,
            "total_value": row.total_value, "unit_value": unit_value,
            "dimensions": dimensions,
        }
        missing_fields = tuple(name for name, value in fields.items() if value is None)
        refined_rows.append(replace(
            row, quantity=quantity, unit_value=unit_value, dimensions=dimensions, missing_fields=missing_fields
        ))
    return tuple(refined_rows), tuple(reports)


def refine_windowhub_ocr_table_lp(
    rows: Iterable[WindowHubOCRTableRow],
    screenshot_or_image: Any,
    engine: Callable[[np.ndarray], Any],
    *,
    lp_x_min: int = 100,
    lp_x_max: int = 160,
    lp_y_min: int = 202,
    lp_y_max: int = 380,
    min_confidence: float = 0.85,
    scale: int = 5,
    padding: int = 25,
    row_tolerance: float = 7.5,
) -> tuple[tuple[WindowHubOCRTableRow, ...], tuple[WindowHubOCRFieldRefinement, ...]]:
    """Recover LP from full-column color/Otsu OCR; preserve existing values."""
    input_rows = tuple(rows)
    if not input_rows or all(row.lp is not None for row in input_rows):
        return input_rows, ()

    image = _normalize_image(screenshot_or_image)
    height, width = image.shape[:2]
    x0, x1 = max(0, lp_x_min), min(width, lp_x_max)
    y0, y1 = max(0, lp_y_min), min(height, lp_y_max)
    if x1 <= x0 or y1 <= y0:
        raise ValueError("LP column crop is outside the screenshot bounds")
    if scale < 1 or padding < 0:
        raise ValueError("scale must be >= 1 and padding must be >= 0")

    crop = image[y0:y1, x0:x1]
    enlarged = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(enlarged, cv2.COLOR_BGR2GRAY)
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variants = (
        ("color", cv2.copyMakeBorder(enlarged, padding, padding, padding, padding, cv2.BORDER_CONSTANT, value=(255, 255, 255))),
        ("otsu", cv2.copyMakeBorder(otsu, padding, padding, padding, padding, cv2.BORDER_CONSTANT, value=255)),
    )

    candidates: list[tuple[int, float, str, float]] = []
    for source, variant_image in variants:
        result = engine(variant_image)
        texts = getattr(result, "txts", None)
        scores = getattr(result, "scores", None)
        boxes = getattr(result, "boxes", None)
        if texts is None or boxes is None:
            continue
        for index, raw_text in enumerate(texts):
            text = str(raw_text).strip() if raw_text is not None else ""
            if not re.fullmatch(r"\d{1,3}", text) or index >= len(boxes):
                continue
            lp_value = int(text)
            if not 1 <= lp_value <= 999:
                continue
            try:
                confidence = float(scores[index]) if scores is not None and index < len(scores) else 0.0
                points = np.asarray(boxes[index], dtype=float).reshape(-1, 2)
            except (TypeError, ValueError, IndexError):
                continue
            if (
                not math.isfinite(confidence)
                or not 0.0 <= confidence <= 1.0
                or confidence < min_confidence
                or not points.size
                or not np.isfinite(points).all()
            ):
                continue
            center_x = float(np.mean(points[:, 0]))
            center_y = float(np.mean(points[:, 1]))
            if not (
                padding <= center_x <= padding + (x1 - x0) * scale
                and padding <= center_y <= padding + (y1 - y0) * scale
            ):
                continue
            screenshot_x = x0 + (center_x - padding) / scale
            screenshot_y = y0 + (center_y - padding) / scale
            if lp_x_min <= screenshot_x <= lp_x_max:
                candidates.append((lp_value, confidence, source, screenshot_y))

    detections_by_row: list[list[tuple[int, float, str, float]]] = [[] for _ in input_rows]
    for candidate in candidates:
        nearest = min(range(len(input_rows)), key=lambda idx: abs(input_rows[idx].center_y - candidate[3]))
        if abs(input_rows[nearest].center_y - candidate[3]) <= row_tolerance:
            detections_by_row[nearest].append(candidate)

    # First collect the best per-row candidate, then check uniqueness across
    # the whole table. Two rows must not both receive the same LP simply
    # because the OCR engine confidently misread one of them.
    row_candidate_info: dict[int, tuple[set[int], tuple[str, ...], float]] = {}
    proposals_by_value: dict[int, list[int]] = {}
    fixed_lp_values = {row.lp for row in input_rows if row.lp is not None}
    for index, row in enumerate(input_rows):
        if row.lp is not None:
            continue
        row_candidates = detections_by_row[index]
        distinct_values = {item[0] for item in row_candidates}
        sources = tuple(sorted({item[2] for item in row_candidates}))
        confidence = max((item[1] for item in row_candidates), default=0.0)
        row_candidate_info[index] = (distinct_values, sources, confidence)
        if len(distinct_values) == 1:
            candidate_value = next(iter(distinct_values))
            proposals_by_value.setdefault(candidate_value, []).append(index)

    refined_rows: list[WindowHubOCRTableRow] = []
    reports: list[WindowHubOCRFieldRefinement] = []
    for index, row in enumerate(input_rows):
        if row.lp is not None:
            refined_rows.append(row)
            continue

        distinct_values, sources, confidence = row_candidate_info[index]
        if len(distinct_values) > 1:
            value, updated = None, row
            accepted, reason = False, "conflicting_candidates"
        elif not distinct_values:
            value, updated = None, row
            accepted, reason = False, "no_valid_candidate"
        else:
            candidate_value = next(iter(distinct_values))
            value = candidate_value
            if candidate_value in fixed_lp_values:
                updated = row
                accepted, reason = False, "duplicate_lp_existing_row"
            elif len(proposals_by_value[candidate_value]) > 1:
                updated = row
                accepted, reason = False, "duplicate_lp_across_rows"
            else:
                updated = replace(row, lp=candidate_value, lp_source="ocr_column")
                accepted, reason = True, "unique_valid_candidate"

        fields = {
            "lp": updated.lp, "quantity": updated.quantity, "article": updated.article,
            "total_value": updated.total_value, "unit_value": updated.unit_value,
            "dimensions": updated.dimensions,
        }
        missing_fields = tuple(name for name, field_value in fields.items() if field_value is None)
        updated = replace(updated, missing_fields=missing_fields)
        refined_rows.append(updated)
        reports.append(WindowHubOCRFieldRefinement(
            row_index=row.row_index, field="lp", previous_value=row.lp,
            candidate_value=value, accepted=accepted, confidence=confidence,
            sources=sources, reason=reason,
        ))
    return tuple(refined_rows), tuple(reports)
