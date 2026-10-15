"""Conservative reconstruction of WindowHub table rows from OCR elements."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Iterable


@dataclass(frozen=True)
class WindowHubOCRTableRow:
    row_index: int
    lp: int | None
    lp_source: str
    quantity: int | None
    article: str | None
    total_value: str | None
    unit_value: str | None
    dimensions: str | None
    center_y: float = field(repr=False)
    missing_fields: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        return not self.missing_fields

    def to_payload(self) -> dict[str, object]:
        """Return model-safe table data without screen coordinates."""
        return {
            "row_index": self.row_index,
            "lp": self.lp,
            "lp_source": self.lp_source,
            "quantity": self.quantity,
            "article": self.article,
            "total_value": self.total_value,
            "unit_value": self.unit_value,
            "dimensions": self.dimensions,
            "complete": self.complete,
            "missing_fields": list(self.missing_fields),
        }


def _center_y(element: object) -> float:
    return float(getattr(element, "y", 0)) + float(getattr(element, "height", 0)) / 2


def _confidence(element: object) -> float:
    try:
        value = float(getattr(element, "confidence", 1.0))
    except (TypeError, ValueError):
        return 0.0
    return value if 0.0 <= value <= 1.0 else 0.0


def _parse_money(text: str) -> str | None:
    value = re.sub(r"\s+", "", text)
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+,\d{2}", value):
        value = value.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d+,\d{2}", value):
        value = value.replace(",", ".")
    if re.fullmatch(r"\d+\.\d{2}", value):
        return value
    return None


def _parse_dimensions(text: str) -> str | None:
    value = re.sub(r"\s+", "", text)
    match = re.search(r"(?<!\d)(\d{2,4})[xX×Îî](\d{2,4})(?!\d)", value)
    if not match:
        return None
    return f"{match.group(1)} x {match.group(2)}"




def _cluster_price_column_centers(
    items: list[dict[str, object]],
    *,
    min_center_y: float,
    max_center_y: float,
) -> list[float]:
    """Infer regular monetary columns from repeated price detections.

    OCR coordinates refer to the left edge of each text box. Long price strings
    can therefore have different x values, but the center of each box is a
    stable column signal. Cluster box centers, not left edges.
    """
    centers = sorted(
        float(item["x"]) + float(item.get("width", 0)) / 2
        for item in items
        if 300 <= float(item["x"]) < 900
        and min_center_y <= float(item["y"]) <= max_center_y
        and _parse_money(str(item["text"])) is not None
    )
    clusters: list[list[float]] = []
    for x in centers:
        if clusters and x - sum(clusters[-1]) / len(clusters[-1]) <= 42:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    # A single accidental monetary value must not switch the entire layout.
    return [sum(cluster) / len(cluster) for cluster in clusters if len(cluster) >= 2]


def _header_price_column_centers(
    items: list[dict[str, object]],
    *,
    min_header_y: float = 155.0,
    max_header_y: float = 212.0,
) -> list[float]:
    """Detect stable price columns from OCR header labels when available.

    This is especially important for a short/single-row offer: repeated price
    values alone cannot distinguish total, per-unit, and service columns when
    each column contains only one amount. Header text remains weak geometric
    evidence; values are still accepted only by the normal conservative parser.
    """
    role_values: dict[str, list[float]] = {
        "total": [],
        "unit": [],
        "service": [],
    }
    for item in items:
        try:
            x = float(item["x"])
            y = float(item["y"])
            width = float(item.get("width", 0))
            raw_text = str(item["text"])
        except (KeyError, TypeError, ValueError):
            continue
        if not 300 <= x < 900 or not min_header_y <= y <= max_header_y:
            continue

        normalized = unicodedata.normalize("NFKD", raw_text.casefold())
        normalized = "".join(
            char for char in normalized if not unicodedata.combining(char)
        )
        center_x = x + width / 2
        if "warto" in normalized:
            role = "unit" if "szt" in normalized else "total"
            role_values[role].append(center_x)
        if "monta" in normalized:
            role_values["service"].append(center_x)

    def dominant_center(values: list[float]) -> float | None:
        if not values:
            return None
        clusters: list[list[float]] = []
        for value in sorted(values):
            if clusters and value - sum(clusters[-1]) / len(clusters[-1]) <= 32:
                clusters[-1].append(value)
            else:
                clusters.append([value])
        best = max(clusters, key=lambda cluster: (len(cluster), -cluster[0]))
        return sum(best) / len(best)

    total_center = dominant_center(role_values["total"])
    unit_center = dominant_center(role_values["unit"])
    if (
        total_center is None
        or unit_center is None
        or total_center >= unit_center
        or unit_center - total_center < 35
    ):
        return []

    centers = [total_center, unit_center]
    service_center = dominant_center(role_values["service"])
    if service_center is not None and service_center > unit_center + 24:
        centers.append(service_center)
    return centers


def _layout_from_normalized_items(
    items: list[dict[str, object]],
    *,
    article_x_min: float = 185,
    article_x_max: float = 380,
    total_x_min: float = 380,
    total_x_max: float = 500,
    unit_x_min: float = 500,
    unit_x_max: float = 600,
    min_center_y: float = 200,
    max_center_y: float = 380,
) -> dict[str, object]:
    # Header text is the strongest available column cue when the current offer
    # has too few data rows to form repeated monetary clusters.
    centers = _header_price_column_centers(items)
    source = "header_text" if centers else "fixed_defaults"
    if not centers:
        centers = _cluster_price_column_centers(
            items, min_center_y=min_center_y, max_center_y=max_center_y
        )
        if len(centers) >= 2:
            source = "repeated_price_values"
    adaptive = len(centers) >= 2
    effective_article_x_max = article_x_max
    effective_total_x_min = total_x_min
    effective_total_x_max = total_x_max
    effective_unit_x_min = unit_x_min
    effective_unit_x_max = unit_x_max
    if adaptive:
        # The first two repeated monetary columns are totals and unit values.
        # A third or later column (for example "Montaż brutto") is separate.
        first, second = centers[0], centers[1]
        effective_article_x_max = max(
            article_x_min + 1, int(first - 38)
        )
        effective_total_x_min = int(first - 42)
        effective_total_x_max = int((first + second) / 2)
        effective_unit_x_min = effective_total_x_max
        effective_unit_x_max = int(second + 42)
    return {
        "adaptive_price_columns": adaptive,
        "price_column_source": source,
        "price_column_centers": centers,
        "article_x_max": effective_article_x_max,
        "total_x_min": effective_total_x_min,
        "total_x_max": effective_total_x_max,
        "unit_x_min": effective_unit_x_min,
        "unit_x_max": effective_unit_x_max,
    }


def infer_windowhub_ocr_table_column_layout(
    ocr_elements: Iterable[object],
    *,
    article_x_min: float = 185,
    article_x_max: float = 380,
    total_x_min: float = 380,
    total_x_max: float = 500,
    unit_x_min: float = 500,
    unit_x_max: float = 600,
    min_center_y: float = 200,
    max_center_y: float = 380,
    min_confidence: float = 0.35,
) -> dict[str, object]:
    """Infer repeated monetary columns and the correct image crops."""
    items: list[dict[str, object]] = []
    for element in ocr_elements:
        text = str(getattr(element, "label", "") or "").strip()
        confidence = _confidence(element)
        if not text or confidence < min_confidence:
            continue
        try:
            x = float(getattr(element, "x"))
            y = _center_y(element)
            width = float(getattr(element, "width", 0))
        except (TypeError, ValueError, AttributeError):
            continue
        if x < 0 or y < 0:
            continue
        items.append({"x": x, "y": y, "width": width, "text": text, "confidence": confidence})
    return _layout_from_normalized_items(
        items,
        article_x_min=article_x_min,
        article_x_max=article_x_max,
        total_x_min=total_x_min,
        total_x_max=total_x_max,
        unit_x_min=unit_x_min,
        unit_x_max=unit_x_max,
        min_center_y=min_center_y,
        max_center_y=max_center_y,
    )



def _assign_unit_price_detections(
    anchors: list[dict[str, object]],
    detections: list[dict[str, object]],
    tolerance: float,
) -> list[dict[str, object] | None]:
    """Assign unit-price OCR detections to rows with order-preserving matching.

    A single unit-price token may fill at most one row, and a row may receive
    at most one token from this column. When several equally good assignments
    exist, the ambiguous token is left unresolved rather than forced onto the
    first row.
    """
    assigned: list[dict[str, object] | None] = [None] * len(anchors)
    if not anchors or not detections:
        return assigned

    row_order = sorted(
        range(len(anchors)), key=lambda index: float(anchors[index]["y"])
    )
    ordered_detections = sorted(
        detections,
        key=lambda item: (float(item["y"]), -float(item["confidence"])),
    )

    def quality(score: tuple[int, float, float]) -> tuple[int, float, float]:
        matched, distance_sum, confidence_sum = score
        return (-matched, round(distance_sum, 6), -round(confidence_sum, 6))

    @lru_cache(maxsize=None)
    def solve(
        row_position: int, detection_position: int
    ) -> tuple[
        tuple[int, float, float],
        dict[int, set[int | None]],
    ]:
        if detection_position >= len(ordered_detections):
            return (0, 0.0, 0.0), {}
        if row_position >= len(row_order):
            return (
                (0, 0.0, 0.0),
                {index: {None} for index in range(
                    detection_position, len(ordered_detections)
                )},
            )

        candidates: list[
            tuple[tuple[int, float, float], dict[int, set[int | None]]]
        ] = []

        # A row may have no usable unit-price token.
        candidates.append(solve(row_position + 1, detection_position))

        # A detection may be OCR noise or a duplicate and remain unused.
        skipped_score, skipped_options = solve(
            row_position, detection_position + 1
        )
        skipped_options = {
            index: set(values) for index, values in skipped_options.items()
        }
        skipped_options[detection_position] = {None}
        candidates.append((skipped_score, skipped_options))

        row_index = row_order[row_position]
        detection = ordered_detections[detection_position]
        distance = abs(
            float(anchors[row_index]["y"]) - float(detection["y"])
        )
        if distance <= tolerance:
            matched_score, matched_options = solve(
                row_position + 1, detection_position + 1
            )
            matched_options = {
                index: set(values) for index, values in matched_options.items()
            }
            matched_options[detection_position] = {row_index}
            candidates.append(
                (
                    (
                        matched_score[0] + 1,
                        matched_score[1] + distance,
                        matched_score[2] + float(detection["confidence"]),
                    ),
                    matched_options,
                )
            )

        best_quality = min(quality(score) for score, _ in candidates)
        best_score = next(
            score for score, _ in candidates if quality(score) == best_quality
        )
        possible: dict[int, set[int | None]] = {}
        for score, options in candidates:
            if quality(score) != best_quality:
                continue
            for index, values in options.items():
                possible.setdefault(index, set()).update(values)
        return best_score, possible

    _, possible_assignments = solve(0, 0)
    for detection_index, row_options in possible_assignments.items():
        if len(row_options) != 1:
            continue
        row_index = next(iter(row_options))
        if row_index is not None:
            assigned[row_index] = ordered_detections[detection_index]
    return assigned


def parse_windowhub_ocr_table(
    ocr_elements: Iterable[object],
    *,
    anchor_x_max: float = 180,
    article_x_min: float = 185,
    article_x_max: float = 380,
    total_x_min: float = 380,
    total_x_max: float = 500,
    unit_x_min: float = 500,
    unit_x_max: float = 600,
    dimensions_x_min: float = 850,
    dimensions_x_max: float = 1350,
    min_center_y: float = 200,
    max_center_y: float = 380,
    row_tolerance: float = 7.5,
    min_confidence: float = 0.35,
) -> tuple[WindowHubOCRTableRow, ...]:
    """Parse text detections in a known table region.

    Coordinates are screenshot-local. If LP anchors are unavailable, prices
    define row order but never become invented LP values.
    """
    items: list[dict[str, object]] = []
    for element in ocr_elements:
        raw_label = getattr(element, "label", None)
        if raw_label is None:
            continue
        text = str(raw_label).strip()
        confidence = _confidence(element)
        if not text or confidence < min_confidence:
            continue
        try:
            x = float(getattr(element, "x"))
            center_y = _center_y(element)
        except (TypeError, ValueError, AttributeError):
            continue
        if not (x >= 0 and center_y >= 0):
            continue
        items.append({"x": x, "y": center_y, "width": float(getattr(element, "width", 0)), "text": text, "confidence": confidence})

    layout = _layout_from_normalized_items(
        items,
        article_x_min=article_x_min,
        article_x_max=article_x_max,
        total_x_min=total_x_min,
        total_x_max=total_x_max,
        unit_x_min=unit_x_min,
        unit_x_max=unit_x_max,
        min_center_y=min_center_y,
        max_center_y=max_center_y,
    )
    if layout["adaptive_price_columns"]:
        centers = list(layout["price_column_centers"])
        second_center = centers[1]
        third_center = centers[2] if len(centers) >= 3 else None
        for item in items:
            x = float(item["x"]) + float(item.get("width", 0)) / 2
            y = float(item["y"])
            if (
                not 300 <= x < 900
                or not min_center_y <= y <= max_center_y
                or _parse_money(str(item["text"])) is None
            ):
                continue
            distances = [abs(x - center) for center in centers]
            column_index = min(range(len(centers)), key=lambda i: distances[i])
            if distances[column_index] > 55:
                continue
            # Normalize the first two detected columns to stable parser bands.
            # Every later monetary column is intentionally excluded.
            if column_index == 0:
                item["x"] = total_x_min + 40
            elif column_index == 1:
                item["x"] = unit_x_min + 30
            else:
                item["x"] = max(unit_x_max + 100, 800)

    lp_by_row: list[list[dict[str, object]]] = []
    for item in items:
        x = float(item["x"])
        y = float(item["y"])
        text = str(item["text"])
        if (
            x < anchor_x_max
            and min_center_y <= y <= max_center_y
            and re.fullmatch(r"\d{1,3}", text)
        ):
            value = int(text)
            if value > 0:
                lp_by_row.append({**item, "lp": value})
    lp_by_row.sort(key=lambda item: float(item["y"]))

    # Price detections anchor physical table rows. Prefer the net-total
    # column when present, but use the unit-price column as a fallback so a
    # missing total-price OCR token does not erase an otherwise visible row.
    total_price_anchors = [
        {**item, "lp": None, "anchor_source": "total_value"}
        for item in items
        if total_x_min <= float(item["x"]) < total_x_max
        and min_center_y <= float(item["y"]) <= max_center_y
        and _parse_money(str(item["text"])) is not None
    ]
    unit_price_anchors = [
        {**item, "lp": None, "anchor_source": "unit_value"}
        for item in items
        if unit_x_min <= float(item["x"]) < unit_x_max
        and min_center_y <= float(item["y"]) <= max_center_y
        and _parse_money(str(item["text"])) is not None
    ]
    total_price_anchors.sort(
        key=lambda item: (float(item["y"]), -float(item["confidence"]))
    )
    unit_price_anchors.sort(
        key=lambda item: (float(item["y"]), -float(item["confidence"]))
    )

    # Deduplicate total-column detections first so they remain the preferred
    # row centers when both price columns have OCR output.
    unique_anchors: list[dict[str, object]] = []
    for anchor in total_price_anchors:
        if not any(
            abs(float(anchor["y"]) - float(previous["y"])) < 5
            for previous in unique_anchors
        ):
            unique_anchors.append(anchor)

    # Remove duplicate unit-price detections from the same physical row.
    unique_unit_anchors: list[dict[str, object]] = []
    for anchor in unit_price_anchors:
        if not any(
            abs(float(anchor["y"]) - float(previous["y"])) < 5
            for previous in unique_unit_anchors
        ):
            unique_unit_anchors.append(anchor)

    # A unit-price token within row_tolerance of a total anchor normally belongs
    # to that existing row. Exception: independent non-price columns may cluster
    # closer to the unit-price token, proving it is the best available anchor
    # for a separate row whose total-price OCR is missing.
    def _support_column(x: float) -> str | None:
        if 0 <= x < anchor_x_max:
            return "lp"
        if article_x_min <= x < article_x_max:
            return "article"
        if dimensions_x_min <= x < dimensions_x_max:
            return "dimensions"
        return None

    for anchor in unique_unit_anchors:
        candidate_y = float(anchor["y"])
        nearby_anchors = [
            previous for previous in unique_anchors
            if abs(candidate_y - float(previous["y"])) <= row_tolerance
        ]
        if not nearby_anchors:
            unique_anchors.append(anchor)
            continue

        supporting_columns: set[str] = set()
        for item in items:
            column = _support_column(float(item["x"]))
            if column is None:
                continue
            item_y = float(item["y"])
            candidate_distance = abs(item_y - candidate_y)
            if candidate_distance > row_tolerance:
                continue
            nearest_existing_distance = min(
                abs(item_y - float(previous["y"]))
                for previous in unique_anchors
            )
            if candidate_distance + 1.0 < nearest_existing_distance:
                supporting_columns.add(column)

        if len(supporting_columns) >= 2:
            unique_anchors.append(anchor)

    unique_anchors.sort(key=lambda item: float(item["y"]))

    if not unique_anchors:
        return ()

    # Assign each LP detection to one physical row only. Independently querying
    # every row can otherwise attach one halfway-positioned digit to two rows.
    lp_candidates_by_anchor: list[list[dict[str, object]]] = [
        [] for _ in unique_anchors
    ]
    ambiguous_anchor_indices: set[int] = set()
    assignment_margin = 1.0

    for lp_item in lp_by_row:
        lp_y = float(lp_item["y"])
        distances = [
            abs(lp_y - float(anchor["y"])) for anchor in unique_anchors
        ]
        eligible = [
            (index, distance)
            for index, distance in enumerate(distances)
            if distance <= row_tolerance
        ]
        if not eligible:
            continue

        best_distance = min(distance for _, distance in eligible)
        near_best = [
            index
            for index, distance in eligible
            if distance - best_distance <= assignment_margin
        ]
        if len(near_best) != 1:
            # A digit close to the boundary between rows is not safe evidence
            # for either row; leave every affected assignment unresolved.
            ambiguous_anchor_indices.update(near_best)
            continue
        lp_candidates_by_anchor[near_best[0]].append(lp_item)

    for index, anchor in enumerate(unique_anchors):
        candidates = lp_candidates_by_anchor[index]
        values = {int(item["lp"]) for item in candidates}
        if index in ambiguous_anchor_indices or len(values) != 1:
            anchor["lp"] = None
            anchor["lp_source"] = "price_column_row_order"
        elif values:
            anchor["lp"] = next(iter(values))
            anchor["lp_source"] = "ocr"
        else:
            anchor["lp"] = None
            anchor["lp_source"] = "price_column_row_order"

    # LP position numbers should identify distinct rows. If OCR produces a
    # duplicate, do not let both values look authoritative downstream.
    lp_rows_by_value: dict[int, list[int]] = {}
    for index, anchor in enumerate(unique_anchors):
        value = anchor.get("lp")
        if value is not None:
            lp_rows_by_value.setdefault(int(value), []).append(index)
    for duplicate_indices in lp_rows_by_value.values():
        if len(duplicate_indices) > 1:
            for index in duplicate_indices:
                unique_anchors[index]["lp"] = None
                unique_anchors[index]["lp_source"] = "price_column_row_order"

    for row_index, anchor in enumerate(unique_anchors, start=1):
        anchor["row_index"] = row_index

    assigned: list[list[dict[str, object]]] = [[] for _ in unique_anchors]
    unit_price_items = [
        item
        for item in items
        if unit_x_min <= float(item["x"]) < unit_x_max
        and _parse_money(str(item["text"])) is not None
    ]
    unit_items_by_row = _assign_unit_price_detections(
        unique_anchors, unit_price_items, row_tolerance
    )
    for row_index, unit_item in enumerate(unit_items_by_row):
        if unit_item is not None:
            assigned[row_index].append(unit_item)

    for item in items:
        x = float(item["x"])
        if (
            unit_x_min <= x < unit_x_max
            and _parse_money(str(item["text"])) is not None
        ):
            # This column is assigned separately with one-to-one row matching.
            continue
        y = float(item["y"])
        nearest_index = min(
            range(len(unique_anchors)),
            key=lambda index: abs(y - float(unique_anchors[index]["y"])),
        )
        if abs(y - float(unique_anchors[nearest_index]["y"])) <= row_tolerance:
            assigned[nearest_index].append(item)

    rows: list[WindowHubOCRTableRow] = []
    for anchor, row_items in zip(unique_anchors, assigned):
        quantities: set[int] = set()
        articles: list[str] = []
        totals: list[tuple[float, str]] = []
        units: list[tuple[float, str]] = []
        dimensions: list[tuple[float, str]] = []

        for item in row_items:
            x = float(item["x"])
            text = str(item["text"])
            if article_x_min <= x < article_x_max:
                match = re.fullmatch(r"\s*(\d+)\s*(.*?)\s*", text)
                if match:
                    quantity_text, suffix = match.group(1), match.group(2).strip()
                    if int(quantity_text) > 0:
                        quantities.add(int(quantity_text))
                    if suffix:
                        articles.append(suffix)
                else:
                    articles.append(text)
            elif total_x_min <= x < total_x_max:
                money = _parse_money(text)
                if money is not None:
                    totals.append((x, money))
            elif unit_x_min <= x < unit_x_max:
                money = _parse_money(text)
                if money is not None:
                    units.append((x, money))
            elif dimensions_x_min <= x < dimensions_x_max:
                parsed = _parse_dimensions(text)
                if parsed is not None:
                    dimensions.append((x, parsed))

        quantity = next(iter(quantities)) if len(quantities) == 1 else None
        article = " ".join(dict.fromkeys(articles)) or None
        total = min(totals)[1] if totals else None
        unit = min(units)[1] if units else None
        dimension = min(dimensions)[1] if dimensions else None
        lp = int(anchor["lp"]) if anchor.get("lp") is not None else None
        fields = {
            "lp": lp,
            "quantity": quantity,
            "article": article,
            "total_value": total,
            "unit_value": unit,
            "dimensions": dimension,
        }
        missing = tuple(name for name, value in fields.items() if value is None)
        rows.append(
            WindowHubOCRTableRow(
                row_index=int(anchor["row_index"]),
                lp=lp,
                lp_source=str(anchor["lp_source"]),
                quantity=quantity,
                article=article,
                total_value=total,
                unit_value=unit,
                dimensions=dimension,
                center_y=float(anchor["y"]),
                missing_fields=missing,
            )
        )
    return tuple(rows)
