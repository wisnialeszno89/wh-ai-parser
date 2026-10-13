"""Conservative local OCR recovery for incomplete WindowHub table rows."""

from __future__ import annotations

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


def _quantity_candidates(
    variants: Iterable[tuple[str, list[tuple[str, float]]]],
    expected_article: str,
    *,
    min_confidence: float,
) -> list[tuple[int, float, str]]:
    expected = _normalize_article(expected_article)
    candidates: list[tuple[int, float, str]] = []
    if not expected:
        return candidates
    for source, items in variants:
        separate_quantities: list[tuple[int, float]] = []
        matching_articles: list[tuple[float, str]] = []
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
                    separate_quantities.append((quantity, confidence))
            if _normalize_article(text) == expected:
                matching_articles.append((confidence, text))
        if separate_quantities and matching_articles:
            for quantity, quantity_confidence in separate_quantities:
                for article_confidence, _ in matching_articles:
                    candidates.append((quantity, min(quantity_confidence, article_confidence), source))
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
) -> tuple[tuple[WindowHubOCRTableRow, ...], tuple[WindowHubOCRFieldRefinement, ...]]:
    """Recover missing quantity/unit-price fields; do not overwrite existing values."""
    input_rows = tuple(rows)
    if not input_rows or all(row.quantity is not None and row.gross_unit is not None for row in input_rows):
        return input_rows, ()
    image = _normalize_image(screenshot_or_image)
    height, width = image.shape[:2]
    refined_rows: list[WindowHubOCRTableRow] = []
    reports: list[WindowHubOCRFieldRefinement] = []

    for row in input_rows:
        quantity = row.quantity
        gross_unit = row.gross_unit
        center_y = int(round(row.center_y))
        y0 = max(0, center_y - row_half_height)
        y1 = min(height, center_y + row_half_height)
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
        if gross_unit is None:
            x0 = max(0, unit_x_min)
            x1 = min(width, unit_x_max)
            variants = _read_variants(engine, image[y0:y1, x0:x1], scale=scale)
            candidates = _money_candidates(variants, min_confidence=money_min_confidence)
            value, confidence, sources, reason = _resolve_candidates(candidates)
            accepted = value is not None
            if accepted:
                gross_unit = str(value)
            reports.append(WindowHubOCRFieldRefinement(
                row_index=row.row_index, field="gross_unit", previous_value=row.gross_unit,
                candidate_value=value, accepted=accepted, confidence=confidence,
                sources=sources, reason=reason,
            ))
        fields = {
            "lp": row.lp, "quantity": quantity, "article": row.article,
            "gross_total": row.gross_total, "gross_unit": gross_unit,
            "dimensions": row.dimensions,
        }
        missing_fields = tuple(name for name, value in fields.items() if value is None)
        refined_rows.append(replace(
            row, quantity=quantity, gross_unit=gross_unit, missing_fields=missing_fields
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
    lp_y_max: int = 340,
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
            if confidence < min_confidence or not points.size or not np.isfinite(points).all():
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

    refined_rows: list[WindowHubOCRTableRow] = []
    reports: list[WindowHubOCRFieldRefinement] = []
    for index, row in enumerate(input_rows):
        if row.lp is not None:
            refined_rows.append(row)
            continue
        row_candidates = detections_by_row[index]
        distinct_values = {item[0] for item in row_candidates}
        sources = tuple(sorted({item[2] for item in row_candidates}))
        confidence = max((item[1] for item in row_candidates), default=0.0)
        if len(distinct_values) == 1:
            value = next(iter(distinct_values))
            updated = replace(row, lp=value, lp_source="ocr_column")
            accepted, reason = True, "unique_valid_candidate"
        elif len(distinct_values) > 1:
            value, updated = None, row
            accepted, reason = False, "conflicting_candidates"
        else:
            value, updated = None, row
            accepted, reason = False, "no_valid_candidate"
        fields = {
            "lp": updated.lp, "quantity": updated.quantity, "article": updated.article,
            "gross_total": updated.gross_total, "gross_unit": updated.gross_unit,
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
