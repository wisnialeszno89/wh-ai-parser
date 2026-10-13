"""Multi-offer synthetic regression suite for WindowHub OCR table reconstruction.

These tests validate parser/refiner behavior across independent synthetic offers,
not just one real OFR screen. OCR-derived values remain tentative observations.
"""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from app.agent.perception.windowhub_ocr_table_parser import (
    parse_windowhub_ocr_table,
)
from app.agent.perception.windowhub_ocr_table_pipeline import (
    reconstruct_windowhub_ocr_table_rows,
)
from app.agent.perception.windowhub_ocr_table_refiner import (
    refine_windowhub_ocr_table_lp,
)
from app.agent.perception.windowhub_ocr_table_parser import WindowHubOCRTableRow


def element(label: str, x: int, y: float, confidence: float = 0.99):
    return SimpleNamespace(
        label=label, x=x, y=y - 4, width=max(12, len(label) * 7),
        height=8, confidence=confidence,
    )


def make_offer(lp_values, quantities, *, start_y=223.0, step=14.0):
    """Build an offer fixture; None means the source OCR missed that value."""
    output = []
    for idx, (lp, quantity) in enumerate(zip(lp_values, quantities)):
        y = start_y + idx * step
        if quantity is not None:
            output.append(element(f"{quantity} Okno", 210, y))
        else:
            output.append(element("Okno", 210, y))
        output.extend([
            element(f"{1000 + idx},00", 420, y),
            element(f"{800 + idx},00", 530, y),
            element(f"{1200 + idx}x1350", 1120, y),
        ])
        if lp is not None:
            output.append(element(str(lp), 120, y))
    return output


def test_multiple_offers_parse_independently_without_cross_offer_state():
    # Three different offers: regular sequence, missing LPs, and an LP sequence
    # starting away from one. Parser calls must not leak anchors between offers.
    offers = [
        (make_offer([1, 2, 3], [1, 1, 2], start_y=223, step=14), [1, 2, 3]),
        (make_offer([None, 11, None, 13], [1, 1, 1, 1], start_y=210, step=13), [None, 11, None, 13]),
        (make_offer([20, 21], [2, 3], start_y=245, step=16), [20, 21]),
    ]
    for detections, expected_lp in offers:
        rows = parse_windowhub_ocr_table(detections)
        assert len(rows) == len(expected_lp)
        assert [row.lp for row in rows] == expected_lp
        assert all(row.article == "Okno" for row in rows)
        assert all(row.gross_total is not None for row in rows)
        assert all(row.dimensions is not None for row in rows)


def test_parser_does_not_invent_lp_or_quantity_from_neighboring_rows():
    detections = make_offer([7, None, 9], [1, None, 2])
    rows = parse_windowhub_ocr_table(detections)
    assert [row.lp for row in rows] == [7, None, 9]
    assert [row.quantity for row in rows] == [1, None, 2]
    assert "lp" in rows[1].missing_fields
    assert "quantity" in rows[1].missing_fields


class BoxEngine:
    def __init__(self, results):
        self.results = list(results)

    def __call__(self, image):
        if not self.results:
            raise AssertionError("Unexpected OCR engine call")
        return self.results.pop(0)


def box_for_y(center_y, *, x_min=100, y_min=202, scale=5, padding=25):
    x_center = (124 - x_min) * scale + padding
    y_center = (center_y - y_min) * scale + padding
    return np.asarray([
        [x_center - 5, y_center - 4], [x_center + 5, y_center - 4],
        [x_center + 5, y_center + 4], [x_center - 5, y_center + 4],
    ], dtype=float)


def lp_result(items):
    return SimpleNamespace(
        txts=[text for text, _, _ in items],
        scores=[confidence for _, confidence, _ in items],
        boxes=[box_for_y(y) for _, _, y in items],
    )


def recovered_row(index, y, lp=None):
    missing = ("lp",) if lp is None else ()
    return WindowHubOCRTableRow(
        row_index=index,
        lp=lp,
        lp_source="price_column_row_order" if lp is None else "ocr",
        quantity=1,
        article="Okno",
        gross_total="1000.00",
        gross_unit="800.00",
        dimensions="1200 x 1350",
        center_y=y,
        missing_fields=missing,
    )


def test_multirow_lp_refinement_rejects_duplicates_and_preserves_unique_values():
    rows = (
        recovered_row(1, 223.0, lp=1),
        recovered_row(2, 238.0),
        recovered_row(3, 253.0),
        recovered_row(4, 268.0),
    )
    engine = BoxEngine([
        lp_result([("1", 0.999, 223), ("6", 0.999, 238), ("6", 0.999, 253), ("8", 0.999, 268)]),
        lp_result([("1", 0.999, 223), ("6", 0.999, 238), ("6", 0.999, 253), ("8", 0.999, 268)]),
    ])
    refined, reports = refine_windowhub_ocr_table_lp(
        rows, np.zeros((400, 200, 3), dtype=np.uint8), engine
    )
    assert [row.lp for row in refined] == [1, None, None, 8]
    report_by_row = {report.row_index: report for report in reports}
    assert report_by_row[2].reason == "duplicate_lp_across_rows"
    assert report_by_row[3].reason == "duplicate_lp_across_rows"
    assert report_by_row[4].accepted is True
    assert "lp" in refined[1].missing_fields
    assert "lp" in refined[2].missing_fields


def test_full_pipeline_keeps_rows_separate_between_offer_invocations():
    # A shared engine adapter is stateless across these invocations: each offer
    # must get only the detections in its own input list and screenshot.
    rows_a = parse_windowhub_ocr_table(make_offer([31, 32], [1, 1], start_y=223))
    rows_b = parse_windowhub_ocr_table(make_offer([71, 72, 73], [2, 2, 2], start_y=223))
    assert [r.lp for r in rows_a] == [31, 32]
    assert [r.lp for r in rows_b] == [71, 72, 73]
    assert len(rows_a) == 2
    assert len(rows_b) == 3
