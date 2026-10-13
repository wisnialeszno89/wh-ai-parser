"""Conservative reconstruction of WindowHub table rows from OCR elements."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class WindowHubOCRTableRow:
    row_index: int
    lp: int | None
    lp_source: str
    quantity: int | None
    article: str | None
    gross_total: str | None
    gross_unit: str | None
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
            "gross_total": self.gross_total,
            "gross_unit": self.gross_unit,
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
    match = re.search(r"(?<!\d)(\d{2,4})[xX×](\d{2,4})(?!\d)", value)
    if not match:
        return None
    return f"{match.group(1)} x {match.group(2)}"


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
    dimensions_x_min: float = 1090,
    dimensions_x_max: float = 1260,
    min_center_y: float = 200,
    max_center_y: float = 350,
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
        items.append({"x": x, "y": center_y, "text": text, "confidence": confidence})

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

    # Price detections anchor physical table rows. Prefer the gross-total
    # column when present, but use the unit-price column as a fallback so a
    # missing total-price OCR token does not erase an otherwise visible row.
    total_price_anchors = [
        {**item, "lp": None, "anchor_source": "gross_total"}
        for item in items
        if total_x_min <= float(item["x"]) < total_x_max
        and min_center_y <= float(item["y"]) <= max_center_y
        and _parse_money(str(item["text"])) is not None
    ]
    unit_price_anchors = [
        {**item, "lp": None, "anchor_source": "gross_unit"}
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

    # Total-price detections are the primary row anchors.
    unique_anchors: list[dict[str, object]] = []
    for anchor in total_price_anchors:
        if not any(
            abs(float(anchor["y"]) - float(previous["y"])) < 5
            for previous in unique_anchors
        ):
            unique_anchors.append(anchor)

    # Deduplicate unit-price detections. A nearby total-price anchor wins,
    # preserving the original row center even when price columns drift
    # vertically. Only promote a nearby unit price to a separate row when at
    # least two independent structural columns align clearly to its center.
    unique_unit_anchors: list[dict[str, object]] = []
    for anchor in unit_price_anchors:
        if not any(
            abs(float(anchor["y"]) - float(previous["y"])) < 5
            for previous in unique_unit_anchors
        ):
            unique_unit_anchors.append(anchor)

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
        nearby_total = [
            existing for existing in unique_anchors
            if abs(candidate_y - float(existing["y"])) <= row_tolerance
        ]
        if not nearby_total:
            unique_anchors.append(anchor)
            continue

        # When total anchors are close together, do not split the price columns
        # unless distinct structural evidence is present near this candidate.
        corroborating_columns: set[str] = set()
        for item in items:
            column = _support_column(float(item["x"]))
            if column is None:
                continue
            item_y = float(item["y"])
            if abs(item_y - candidate_y) > row_tolerance:
                continue
            nearest_total = min(
                abs(item_y - float(existing["y"]))
                for existing in unique_anchors
            )
            candidate_distance = abs(item_y - candidate_y)
            if candidate_distance + 1.0 < nearest_total:
                corroborating_columns.add(column)

        if len(corroborating_columns) >= 2:
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
    for item in items:
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
            "gross_total": total,
            "gross_unit": unit,
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
                gross_total=total,
                gross_unit=unit,
                dimensions=dimension,
                center_y=float(anchor["y"]),
                missing_fields=missing,
            )
        )
    return tuple(rows)
