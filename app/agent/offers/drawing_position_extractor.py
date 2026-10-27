"""Conservative layout-aware extraction of dimensions from window drawing sheets.

This module creates reviewable candidates only. It never executes an offer workflow
and it requires visual confirmation because image OCR boxes can be mis-associated.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from statistics import median

from app.agent.adapters.document_ocr import OCRTextRegion
from app.agent.adapters.pdf_document_adapter import PdfPageFinding


_POSITION = re.compile(r"^\s*(?:position|pozycja|pos\.?|позиция)\s*[:#-]?\s*(\d+)\s*$", re.IGNORECASE)
_QUANTITY = re.compile(
    r"^\s*(?:menge|ilość|ilosc|quantity|qty|anzahl|szt\.?|количество)\s*[:=]?\s*(\d+)\s*$",
    re.IGNORECASE,
)
_NUMERIC = re.compile(r"^\s*(\d{2,5})\s*$")


@dataclass(frozen=True)
class DrawingPositionCandidate:
    """One possible item row recovered from a dimensioned drawing."""

    source_alias: str
    page_number: int
    position_number: int
    quantity: int | None
    width_mm: int | None
    height_mm: int | None
    confidence: float | None
    quantity_evidence: str | None
    width_evidence: str | None
    height_evidence: str | None
    issues: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        return (
            self.quantity is not None
            and self.width_mm is not None
            and self.height_mm is not None
            and not self.issues
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "source_alias": self.source_alias,
            "page_number": self.page_number,
            "position_number": self.position_number,
            "quantity": self.quantity,
            "width_mm": self.width_mm,
            "height_mm": self.height_mm,
            "confidence": self.confidence,
            "quantity_evidence": self.quantity_evidence,
            "width_evidence": self.width_evidence,
            "height_evidence": self.height_evidence,
            "complete": self.complete,
            "issues": list(self.issues),
            "requires_visual_review": True,
        }


@dataclass(frozen=True)
class DrawingPositionExtractionResult:
    """Candidate drawing rows; never equivalent to a validated offer."""

    source_alias: str
    page_number: int
    positions: tuple[DrawingPositionCandidate, ...]
    issues: tuple[str, ...] = ()

    @property
    def requires_visual_review(self) -> bool:
        # A reviewer must confirm that the outer dimensions were identified,
        # even when the geometric heuristics found a complete candidate.
        return True

    @property
    def complete(self) -> bool:
        return bool(self.positions) and not self.issues and all(
            position.complete for position in self.positions
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "source_alias": self.source_alias,
            "page_number": self.page_number,
            "positions": [position.to_payload() for position in self.positions],
            "complete_candidates": self.complete,
            "requires_visual_review": True,
            "issues": list(self.issues),
        }


def _center_x(region: OCRTextRegion) -> float:
    return region.x + region.width / 2


def _center_y(region: OCRTextRegion) -> float:
    return region.y + region.height / 2


def _numeric_value(region: OCRTextRegion) -> int | None:
    match = _NUMERIC.fullmatch(region.text.strip())
    if match is None:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _cluster_position_rows(
    regions: list[tuple[int, OCRTextRegion]],
    *,
    max_within_row_gap: float = 140.0,
) -> list[list[tuple[int, OCRTextRegion]]]:
    """Cluster slanted, multi-column Position labels into visual rows."""
    rows: list[list[tuple[int, OCRTextRegion]]] = []
    for item in sorted(regions, key=lambda pair: (_center_y(pair[1]), _center_x(pair[1]))):
        if not rows:
            rows.append([item])
            continue
        prior_center = median(_center_y(region) for _, region in rows[-1])
        if _center_y(item[1]) - prior_center > max_within_row_gap:
            rows.append([item])
        else:
            rows[-1].append(item)
    for row in rows:
        row.sort(key=lambda pair: _center_x(pair[1]))
    return rows


def _partition_dimension_rows(
    regions: list[OCRTextRegion],
    row_count: int,
) -> tuple[list[list[OCRTextRegion]], list[str]]:
    """Split numeric dimension boxes into drawing rows using the largest Y gaps."""
    ordered = sorted(regions, key=lambda region: (_center_y(region), _center_x(region)))
    if row_count < 1 or len(ordered) < row_count:
        return [], ["not_enough_numeric_dimension_regions_to_split_rows"]
    if row_count == 1:
        return [ordered], []

    gaps = [
        (_center_y(ordered[index + 1]) - _center_y(ordered[index]), index)
        for index in range(len(ordered) - 1)
    ]
    selected = sorted(gaps, reverse=True)[: row_count - 1]
    if len(selected) != row_count - 1 or any(gap < 70.0 for gap, _ in selected):
        return [], ["drawing_row_separation_is_ambiguous"]
    cuts = sorted(index for _, index in selected)
    rows: list[list[OCRTextRegion]] = []
    start = 0
    for cut in cuts:
        rows.append(ordered[start : cut + 1])
        start = cut + 1
    rows.append(ordered[start:])
    if len(rows) != row_count or any(not row for row in rows):
        return [], ["drawing_row_separation_is_ambiguous"]
    return rows, []


class DrawingPositionExtractor:
    """Recover width, height, and quantity candidates from OCR box geometry.

    The heuristic expects position labels such as "Position 1", a quantity label
    such as "Menge 4", horizontal overall-width labels, and vertical overall-height
    labels. For missing labels or unclear geometry, it returns issues rather than
    guessing. Results are candidates for a person to verify, never executable facts.
    """

    def extract(self, page: PdfPageFinding) -> DrawingPositionExtractionResult:
        if not isinstance(page, PdfPageFinding):
            raise TypeError("DrawingPositionExtractor requires a PdfPageFinding.")

        position_labels: list[tuple[int, OCRTextRegion]] = []
        quantities: list[tuple[int, OCRTextRegion]] = []
        numeric_regions: list[tuple[int, OCRTextRegion]] = []

        for region in page.ocr_regions:
            position_match = _POSITION.fullmatch(region.text.strip())
            if position_match is not None:
                position_labels.append((int(position_match.group(1)), region))
                continue
            quantity_match = _QUANTITY.fullmatch(region.text.strip())
            if quantity_match is not None:
                quantities.append((int(quantity_match.group(1)), region))
                continue
            value = _numeric_value(region)
            if value is not None and 200 <= value <= 5000:
                numeric_regions.append((value, region))

        if not position_labels:
            return DrawingPositionExtractionResult(
                source_alias=page.source_alias,
                page_number=page.page_number,
                positions=(),
                issues=("no_explicit_position_labels_found",),
            )

        position_rows = _cluster_position_rows(position_labels)
        row_centers = [median(_center_y(region) for _, region in row) for row in position_rows]
        quantities_by_row: list[list[tuple[int, OCRTextRegion]]] = [[] for _ in position_rows]
        for quantity in quantities:
            row_index = min(
                range(len(row_centers)),
                key=lambda index: abs(_center_y(quantity[1]) - row_centers[index]),
            )
            quantities_by_row[row_index].append(quantity)
        for row in quantities_by_row:
            row.sort(key=lambda pair: _center_x(pair[1]))

        issues: list[str] = []
        quantity_map: dict[int, tuple[int, OCRTextRegion]] = {}
        initial_centers_by_row: list[dict[int, float]] = []
        paired_positions_by_row: list[list[tuple[int, OCRTextRegion, int | None, OCRTextRegion | None]]] = []

        for row_index, row in enumerate(position_rows):
            row_quantities = quantities_by_row[row_index]
            if len(row_quantities) != len(row):
                issues.append(
                    f"position_quantity_count_mismatch_in_row_{row_index + 1}"
                )
            paired = []
            x_offsets = [
                _center_x(quantity_region) - _center_x(position_region)
                for (_, position_region), (_, quantity_region) in zip(row, row_quantities)
            ]
            fallback_offset = median(x_offsets) if x_offsets else 0.0
            centers: dict[int, float] = {}
            for index, (position_number, position_region) in enumerate(row):
                if index < len(row_quantities):
                    quantity_value, quantity_region = row_quantities[index]
                    quantity_map[position_number] = (quantity_value, quantity_region)
                    qx = _center_x(quantity_region)
                else:
                    quantity_region = None
                    quantity_value = None
                    qx = _center_x(position_region) + fallback_offset
                centers[position_number] = (_center_x(position_region) + qx) / 2
                paired.append(
                    (position_number, position_region, quantity_value, quantity_region)
                )
            initial_centers_by_row.append(centers)
            paired_positions_by_row.append(paired)

        # Major dimensions (>= 600 mm) establish the vertical bands for drawings.
        major = [
            region
            for value, region in numeric_regions
            if value >= 600
            and (region.width >= region.height * 1.10
                 or region.height >= region.width * 1.10)
        ]
        dimension_rows, row_issues = _partition_dimension_rows(major, len(position_rows))
        issues.extend(row_issues)

        # Store per-position dimension evidence, refined horizontal centers and values.
        dimensions: dict[int, dict[str, tuple[int, OCRTextRegion]]] = {
            number: {} for number, _ in position_labels
        }
        if dimension_rows:
            for row_index, dimension_row in enumerate(dimension_rows):
                paired = paired_positions_by_row[row_index]
                centers = initial_centers_by_row[row_index]
                row_numbers = {number for number, *_ in paired}
                horizontal_by_position: dict[int, list[tuple[int, OCRTextRegion]]] = {
                    number: [] for number in row_numbers
                }
                vertical_by_position: dict[int, list[tuple[int, OCRTextRegion]]] = {
                    number: [] for number in row_numbers
                }

                # Assign horizontal labels first using the Position/Menge row.
                for region in dimension_row:
                    value = _numeric_value(region)
                    if value is None:
                        continue
                    if region.width >= region.height * 1.10:
                        nearest_number = min(
                            row_numbers,
                            key=lambda number: abs(_center_x(region) - centers[number]),
                        )
                        horizontal_by_position[nearest_number].append((value, region))

                # Prefer the greatest horizontal dimension in a cell as the
                # overall width (e.g. 2200 over two internal 1100 sections).
                refined_centers = dict(centers)
                for number, candidates_for_width in horizontal_by_position.items():
                    if not candidates_for_width:
                        continue
                    max_width = max(value for value, _ in candidates_for_width)
                    widest_boxes = [
                        region for value, region in candidates_for_width
                        if value == max_width
                    ]
                    refined_centers[number] = median(
                        _center_x(region) for region in widest_boxes
                    )
                    dimensions[number]["width"] = (max_width, widest_boxes[0])

                # Then assign vertical labels to the refined cell centers and
                # use the greatest value as the overall height, not 1200+210+30.
                for region in dimension_row:
                    value = _numeric_value(region)
                    if value is None or region.height < region.width * 1.10:
                        continue
                    nearest_number = min(
                        row_numbers,
                        key=lambda number: abs(
                            _center_x(region) - refined_centers[number]
                        ),
                    )
                    vertical_by_position[nearest_number].append((value, region))

                for number, candidates_for_height in vertical_by_position.items():
                    if candidates_for_height:
                        dimensions[number]["height"] = max(
                            candidates_for_height, key=lambda item: item[0]
                        )

        candidates: list[DrawingPositionCandidate] = []
        for paired_row in paired_positions_by_row:
            for number, _position_region, quantity_value, quantity_region in paired_row:
                row_issues_for_position: list[str] = []
                width_item = dimensions.get(number, {}).get("width")
                height_item = dimensions.get(number, {}).get("height")
                if quantity_value is None or quantity_region is None:
                    row_issues_for_position.append("quantity_not_found")
                elif quantity_value <= 0:
                    row_issues_for_position.append("quantity_not_positive")
                if width_item is None:
                    row_issues_for_position.append("overall_width_not_found")
                if height_item is None:
                    row_issues_for_position.append("overall_height_not_found")

                evidence_regions = [
                    item for item in (
                        quantity_region,
                        width_item[1] if width_item else None,
                        height_item[1] if height_item else None,
                    ) if item is not None
                ]
                confidence_values = [
                    region.confidence
                    for region in evidence_regions
                    if region.confidence is not None
                ]
                confidence = min(confidence_values) if confidence_values else None

                candidates.append(
                    DrawingPositionCandidate(
                        source_alias=page.source_alias,
                        page_number=page.page_number,
                        position_number=number,
                        quantity=quantity_value,
                        width_mm=width_item[0] if width_item else None,
                        height_mm=height_item[0] if height_item else None,
                        confidence=confidence,
                        quantity_evidence=quantity_region.text if quantity_region else None,
                        width_evidence=width_item[1].text if width_item else None,
                        height_evidence=height_item[1].text if height_item else None,
                        issues=tuple(row_issues_for_position),
                    )
                )

        if any(not candidate.complete for candidate in candidates):
            issues.append("one_or_more_positions_need_manual_field_review")
        return DrawingPositionExtractionResult(
            source_alias=page.source_alias,
            page_number=page.page_number,
            positions=tuple(sorted(candidates, key=lambda item: item.position_number)),
            issues=tuple(dict.fromkeys(issues)),
        )
