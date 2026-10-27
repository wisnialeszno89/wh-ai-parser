from __future__ import annotations

from app.agent.adapters.document_ocr import OCRTextRegion
from app.agent.offers.window_quote_layout import preview_window_quote_layout


def region(text, confidence, x, y, width, height):
    return OCRTextRegion(
        text=text,
        confidence=confidence,
        x=x,
        y=y,
        width=width,
        height=height,
    )


def sample_regions():
    """Representative OCR boxes from a two-row, three-column quote sheet."""
    return (
        region("Position 1", .998, 113, 94, 118, 48),
        region("Menge 3", 1.0, 297, 120, 104, 46),
        region("Position 2", 1.0, 525, 144, 110, 36),
        region("Menge 2", .999, 744, 153, 98, 37),
        region("Position 3", .996, 938, 159, 108, 32),
        region("Menge 1", .998, 1146, 162, 99, 35),
        region("1150", 1.0, 154, 371, 30, 58),
        region("1400", 1.0, 455, 376, 31, 60),
        region("1150", 1.0, 582, 404, 31, 57),
        region("1400", 1.0, 872, 394, 28, 51),
        region("1150", 1.0, 1041, 416, 34, 55),
        region("1400", 1.0, 1243, 401, 28, 51),
        region("1010", 1.0, 289, 563, 61, 36),
        region("900", .94, 710, 584, 58, 33),
        region("600", 1.0, 1131, 593, 46, 29),
        region("Position 4", 1.0, 105, 629, 117, 40),
        region("Menge 1", .993, 291, 644, 100, 37),
        region("Position 5", .997, 517, 657, 108, 31),
        region("Menge 1", .999, 735, 662, 95, 33),
        region("Position 6", .994, 928, 666, 107, 29),
        region("Menge 1", .999, 1135, 667, 98, 36),
        region("2000", 1.0, 285, 785, 62, 33),
        region("2000", 1.0, 1121, 806, 57, 32),
        region("1150", 1.0, 120, 900, 30, 57),
        region("1400", 1.0, 475, 902, 28, 54),
        region("1900", 1.0, 620, 907, 31, 57),
        region("2100", 1.0, 811, 896, 34, 60),
        region("1150", 1.0, 960, 920, 31, 58),
        region("1400", 1.0, 1307, 917, 28, 54),
        region("1000", .985, 206, 1025, 56, 30),
        region("1000", 1.0, 362, 1028, 59, 33),
        region("1000", 1.0, 1041, 1043, 55, 28),
        region("1000", 1.0, 1196, 1046, 54, 28),
        region("950", .997, 702, 1091, 55, 27),
    )


def test_layout_preview_groups_six_positions_without_auto_execution():
    preview = preview_window_quote_layout(sample_regions())

    assert [item.position_number for item in preview.positions] == [1, 2, 3, 4, 5, 6]
    assert [item.quantity for item in preview.positions] == [3, 2, 1, 1, 1, 1]
    assert [item.width_mm for item in preview.positions] == [1010, 900, 600, 2000, 950, 2000]
    assert [item.height_mm for item in preview.positions] == [1400, 1400, 1400, 1400, 2100, 1400]
    assert preview.total_quantity_candidate == 9
    assert preview.complete_position_count == 6
    assert preview.to_payload()["manual_review_required"] is True
    assert preview.to_payload()["automatically_executable"] is False


def test_layout_preview_retains_alternative_dimension_values_for_review():
    preview = preview_window_quote_layout(sample_regions())
    positions = {item.position_number: item for item in preview.positions}

    assert 2000 in positions[4].width_candidates_mm
    assert 1000 in positions[4].width_candidates_mm
    assert 1900 in positions[5].height_candidates_mm
    assert 2100 in positions[5].height_candidates_mm
    assert all(item.limitations for item in preview.positions)


def test_layout_preview_returns_safe_manual_review_when_anchors_missing():
    preview = preview_window_quote_layout((
        region("Menge 2", .99, 100, 100, 90, 30),
        region("1150", .99, 110, 200, 30, 55),
    ))

    assert preview.positions == ()
    assert preview.to_payload()["automatically_executable"] is False
    assert preview.to_payload()["manual_review_required"] is True
