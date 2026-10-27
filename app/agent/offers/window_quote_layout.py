"""Conservative, review-only layout extraction for window quote drawings.

This module deliberately does not create QuoteFacts or authorize execution.
It uses OCR box geometry to propose per-position width/height/quantity
candidates for review. Repeated dimensions, section widths and inner/outer
measurements can occur in technical drawings, so every result requires
human review regardless of OCR confidence.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from statistics import median
from typing import Iterable, Sequence

from app.agent.adapters.document_ocr import OCRTextRegion


_POSITION_RE = re.compile(r"^\s*position\s+(\d+)\s*$", re.IGNORECASE)
_QUANTITY_RE = re.compile(r"^\s*menge\s+(\d+)\s*$", re.IGNORECASE)
_NUMERIC_DIMENSION_RE = re.compile(r"^\s*(\d{3,4})\s*$")


@dataclass(frozen=True)
class WindowQuotePositionCandidate:
    """Candidate dimensions for one drawing position; never auto-executable."""

    position_number: int
    quantity: int | None
    width_mm: int | None
    height_mm: int | None
    width_candidates_mm: tuple[int, ...]
    height_candidates_mm: tuple[int, ...]
    ocr_confidence_min: float | None
    limitations: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return (
            self.quantity is not None
            and self.width_mm is not None
            and self.height_mm is not None
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "position": self.position_number,
            "quantity": self.quantity,
            "width_mm_candidate": self.width_mm,
            "height_mm_candidate": self.height_mm,
            "width_candidates_mm": list(self.width_candidates_mm),
            "height_candidates_mm": list(self.height_candidates_mm),
            "ocr_confidence_min": self.ocr_confidence_min,
            "complete": self.complete,
            "manual_review_required": True,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class WindowQuoteLayoutPreview:
    """Read-only set of position candidates with an unconditional review gate."""

    positions: tuple[WindowQuotePositionCandidate, ...]
    limitations: tuple[str, ...]

    @property
    def total_quantity_candidate(self) -> int | None:
        quantities = [item.quantity for item in self.positions]
        if not quantities or any(value is None for value in quantities):
            return None
        return sum(int(value) for value in quantities if value is not None)

    @property
    def complete_position_count(self) -> int:
        return sum(item.complete for item in self.positions)

    def to_payload(self) -> dict[str, object]:
        return {
            "position_count": len(self.positions),
            "complete_position_count": self.complete_position_count,
            "total_quantity_candidate": self.total_quantity_candidate,
            "manual_review_required": True,
            "automatically_executable": False,
            "positions": [item.to_payload() for item in self.positions],
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class _Anchor:
    number: int
    region: OCRTextRegion


@dataclass(frozen=True)
class _NumericRegion:
    value: int
    region: OCRTextRegion
    orientation: str


def _center_y(item: object) -> float:
    region = getattr(item, "region", None)
    target = region if region is not None else item
    return float(getattr(target, "center_y"))


def _median_y(items: Sequence[object]) -> float:
    return median(_center_y(item) for item in items)


def _split_by_largest_y_gap(
    items: Sequence[object],
    *,
    minimum_gap: float,
) -> list[list[object]]:
    """Split a coordinate sequence into two visual bands only when well separated."""
    ordered = sorted(items, key=_center_y)
    if len(ordered) < 2:
        return [list(ordered)] if ordered else []

    gaps = [
        _center_y(ordered[index + 1])
        - _center_y(ordered[index])
        for index in range(len(ordered) - 1)
    ]
    largest_index = max(range(len(gaps)), key=gaps.__getitem__)
    typical_gap = median(gaps)
    if gaps[largest_index] < max(minimum_gap, typical_gap * 3.0):
        return [list(ordered)]
    return [list(ordered[: largest_index + 1]), list(ordered[largest_index + 1 :])]


def _position_anchors(regions: Sequence[OCRTextRegion]) -> list[_Anchor]:
    anchors = []
    for region in regions:
        match = _POSITION_RE.fullmatch(region.text.strip())
        if match is not None:
            anchors.append(_Anchor(int(match.group(1)), region))
    return sorted(anchors, key=lambda item: (item.region.center_y, item.region.center_x))


def _quantity_anchors(regions: Sequence[OCRTextRegion]) -> list[_Anchor]:
    anchors = []
    for region in regions:
        match = _QUANTITY_RE.fullmatch(region.text.strip())
        if match is not None:
            quantity = int(match.group(1))
            if quantity > 0:
                anchors.append(_Anchor(quantity, region))
    return anchors


def _numeric_regions(regions: Sequence[OCRTextRegion]) -> list[_NumericRegion]:
    values: list[_NumericRegion] = []
    for region in regions:
        match = _NUMERIC_DIMENSION_RE.fullmatch(region.text.strip())
        if match is None:
            continue
        value = int(match.group(1))
        if value <= 0:
            continue
        if region.width >= region.height * 1.1:
            orientation = "horizontal"
        elif region.height >= region.width * 1.1:
            orientation = "vertical"
        else:
            orientation = "ambiguous"
        if orientation != "ambiguous":
            values.append(_NumericRegion(value, region, orientation))
    return values


def _row_groups(anchors: Sequence[_Anchor]) -> list[list[_Anchor]]:
    raw = _split_by_largest_y_gap(
        anchors,
        minimum_gap=100.0,
    )
    return [
        sorted((item for item in row if isinstance(item, _Anchor)),
               key=lambda item: item.region.center_x)
        for row in raw
    ]


def _match_quantities_to_row(
    row: Sequence[_Anchor],
    quantity_anchors: Sequence[_Anchor],
) -> list[_Anchor | None]:
    if not row:
        return []
    row_mid_y = median(anchor.region.center_y for anchor in row)
    row_tolerance = max(
        85.0,
        max(anchor.region.height for anchor in row) * 2.0,
    )
    nearby = [
        item for item in quantity_anchors
        if abs(item.region.center_y - row_mid_y) <= row_tolerance
    ]
    nearby.sort(key=lambda item: item.region.center_x)
    if len(nearby) != len(row):
        # Keep deterministic left-to-right pairing but explicitly mark unmatched
        # quantities as missing; do not borrow a quantity from another row.
        result: list[_Anchor | None] = []
        used: set[int] = set()
        for position in row:
            candidates = [
                item for item in nearby
                if id(item) not in used
                and item.region.center_x > position.region.center_x
            ]
            if not candidates:
                result.append(None)
                continue
            selected = min(
                candidates,
                key=lambda item: (
                    abs(item.region.center_y - position.region.center_y),
                    item.region.center_x - position.region.center_x,
                ),
            )
            used.add(id(selected))
            result.append(selected)
        return result
    return list(nearby)


def _width_anchor(
    position: _Anchor,
    quantity: _Anchor | None,
    horizontal_dimensions: Sequence[_NumericRegion],
) -> _NumericRegion | None:
    if quantity is None:
        return None
    x_left = position.region.center_x
    x_right = quantity.region.center_x
    low, high = sorted((x_left, x_right))
    in_cell = [
        item for item in horizontal_dimensions
        if low <= item.region.center_x <= high
    ]
    if in_cell:
        # A drawing can contain both an overall width and smaller section
        # widths. The largest is only a candidate and is
        # always sent to manual review.
        return max(in_cell, key=lambda item: (item.value, item.region.confidence or 0.0))

    # Fallback only supplies a review candidate; it is not an execution signal.
    estimated_center = x_left + 0.82 * (x_right - x_left)
    nearby = [
        item for item in horizontal_dimensions
        if abs(item.region.center_x - estimated_center) <= 100.0
    ]
    if not nearby:
        return None
    return max(nearby, key=lambda item: (item.value, item.region.confidence or 0.0))


def _height_candidates_for_position(
    width_anchor: _NumericRegion | None,
    vertical_dimensions: Sequence[_NumericRegion],
    all_width_anchors: Sequence[_NumericRegion],
) -> tuple[int, ...]:
    if width_anchor is None:
        return ()
    assigned = [
        item for item in vertical_dimensions
        if min(
            abs(item.region.center_x - other.region.center_x)
            for other in all_width_anchors
        ) >= 0
    ]
    # Assign each vertical measure to the nearest width anchor, which acts as
    # the visual center of its drawing tile.
    assigned = [
        item for item in assigned
        if width_anchor in all_width_anchors
        and min(
            abs(item.region.center_x - other.region.center_x)
            for other in all_width_anchors
        ) == abs(item.region.center_x - width_anchor.region.center_x)
    ]
    return tuple(sorted({item.value for item in assigned}))


def _minimum_confidence(
    regions: Iterable[OCRTextRegion | None],
) -> float | None:
    values = [
        float(region.confidence)
        for region in regions
        if region is not None and region.confidence is not None
    ]
    return min(values) if values else None


def preview_window_quote_layout(
    regions: Iterable[OCRTextRegion],
) -> WindowQuoteLayoutPreview:
    """Propose position-level dimensions from an OCR layout without execution.

    This first version targets quote sheets with position headings and quantity
    labels arranged in visual rows. It selects the largest horizontal and
    vertical numeric measurements in each tile as candidates, retaining other
    measurements for human review. It never creates trusted QuoteFacts.
    """
    region_tuple = tuple(regions)
    positions = _position_anchors(region_tuple)
    quantities = _quantity_anchors(region_tuple)
    numeric = _numeric_regions(region_tuple)
    if not positions:
        return WindowQuoteLayoutPreview(
            positions=(),
            limitations=(
                "No explicit 'Position N' headings were recognized.",
                "No data can be safely grouped without position anchors.",
            ),
        )

    position_rows = _row_groups(positions)
    numeric_rows = _split_by_largest_y_gap(
        numeric,
        minimum_gap=80.0,
    )
    numeric_rows = [
        sorted((item for item in row if isinstance(item, _NumericRegion)),
               key=lambda item: (item.region.center_y, item.region.center_x))
        for row in numeric_rows
    ]

    # Both anchor rows and numeric-dimension bands are ordered top-to-bottom.
    # If their counts differ, dimensions stay unassigned rather than being
    # silently borrowed from a different row.
    dimensions_by_row: list[list[_NumericRegion] | None] = []
    if len(position_rows) == len(numeric_rows):
        dimensions_by_row = [list(row) for row in numeric_rows]
    else:
        dimensions_by_row = [None for _ in position_rows]

    candidates: list[WindowQuotePositionCandidate] = []
    for row_index, row in enumerate(position_rows):
        matched_quantities = _match_quantities_to_row(row, quantities)
        dimension_row = dimensions_by_row[row_index]
        horizontal = (
            [item for item in dimension_row if item.orientation == "horizontal"]
            if dimension_row is not None else []
        )
        vertical = (
            [item for item in dimension_row if item.orientation == "vertical"]
            if dimension_row is not None else []
        )

        width_anchors: list[_NumericRegion] = []
        provisional: list[tuple[_Anchor, _Anchor | None, _NumericRegion | None]] = []
        for position, quantity in zip(row, matched_quantities):
            anchor = _width_anchor(position, quantity, horizontal)
            provisional.append((position, quantity, anchor))
            if anchor is not None:
                width_anchors.append(anchor)

        for position, quantity, width_anchor in provisional:
            limitations = [
                "Layout-based dimension selection is heuristic and is not trusted for automatic offer creation.",
                "Verify the selected overall dimensions against the original drawing.",
            ]
            if quantity is None:
                limitations.append("A matching 'Menge N' quantity label was not found.")
            if width_anchor is None:
                limitations.append("No horizontal dimension could be associated with this position.")
            width_candidates: tuple[int, ...] = ()
            height_candidates: tuple[int, ...] = ()
            if width_anchor is not None:
                nearby_widths = [
                    item for item in horizontal
                    if abs(item.region.center_x - width_anchor.region.center_x) <= 125.0
                ]
                width_candidates = tuple(sorted({item.value for item in nearby_widths}))
                height_candidates = _height_candidates_for_position(
                    width_anchor,
                    vertical,
                    width_anchors,
                )
            width_value = max(width_candidates) if width_candidates else None
            height_value = max(height_candidates) if height_candidates else None
            if not height_candidates:
                limitations.append("No vertical dimension candidate could be associated with this position.")
            if len(width_candidates) > 1 or len(height_candidates) > 1:
                limitations.append("More than one dimension value was detected; confirm overall versus section/inner measurements.")

            used_regions: list[OCRTextRegion | None] = [
                position.region,
                quantity.region if quantity is not None else None,
                width_anchor.region if width_anchor is not None else None,
            ]
            if width_anchor is not None and height_candidates:
                used_regions.extend(
                    item.region for item in vertical
                    if item.value in height_candidates
                    and min(
                        abs(item.region.center_x - other.region.center_x)
                        for other in width_anchors
                    ) == abs(item.region.center_x - width_anchor.region.center_x)
                )
            candidates.append(
                WindowQuotePositionCandidate(
                    position_number=position.number,
                    quantity=quantity.number if quantity is not None else None,
                    width_mm=width_value,
                    height_mm=height_value,
                    width_candidates_mm=width_candidates,
                    height_candidates_mm=height_candidates,
                    ocr_confidence_min=_minimum_confidence(used_regions),
                    limitations=tuple(dict.fromkeys(limitations)),
                )
            )

    if len(position_rows) > 1 and len(position_rows) != len(numeric_rows):
        global_limitations = (
            "Position rows and dimension bands did not align; dimensions were not auto-assigned.",
            "Manual review is required for every position.",
        )
    else:
        global_limitations = (
            "This is a candidate preview only; no fact-validation or offer-creation workflow was invoked.",
            "OCR confidence measures character recognition, not correctness of dimension-to-position mapping.",
        )
    candidates.sort(key=lambda item: item.position_number)
    return WindowQuoteLayoutPreview(
        positions=tuple(candidates),
        limitations=global_limitations,
    )
