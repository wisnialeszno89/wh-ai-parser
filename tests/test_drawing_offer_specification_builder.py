from __future__ import annotations

import pytest

from app.agent.offers.drawing_offer_specification_builder import (
    DrawingOfferSpecificationBuilder,
    ReviewedDrawingPosition,
)
from app.agent.offers.drawing_position_extractor import (
    DrawingPositionCandidate,
    DrawingPositionExtractionResult,
)


def extraction_fixture() -> DrawingPositionExtractionResult:
    rows = (
        (1, 4, 1120, 1440),
        (2, 2, 1100, 1440),
        (3, 2, 700, 1440),
        (4, 1, 2200, 1440),
        (5, 1, 1050, 2170),
        (6, 1, 2200, 1440),
    )
    candidates = tuple(
        DrawingPositionCandidate(
            source_alias="drawing.jpg",
            page_number=1,
            position_number=position,
            quantity=quantity,
            width_mm=width,
            height_mm=height,
            confidence=0.99,
            quantity_evidence=f"Menge {quantity}",
            width_evidence=str(width),
            height_evidence=str(height),
        )
        for position, quantity, width, height in rows
    )
    return DrawingPositionExtractionResult(
        source_alias="drawing.jpg",
        page_number=1,
        positions=candidates,
    )


def reviewed_fixture() -> tuple[ReviewedDrawingPosition, ...]:
    return (
        ReviewedDrawingPosition(1, 1120, 1440, 4, True),
        ReviewedDrawingPosition(2, 1100, 1440, 2, True),
        ReviewedDrawingPosition(3, 700, 1440, 2, True),
        ReviewedDrawingPosition(4, 2200, 1440, 1, True),
        ReviewedDrawingPosition(5, 1050, 2170, 1, True),
        ReviewedDrawingPosition(6, 2200, 1440, 1, True),
    )


def test_reviewed_six_position_drawing_builds_multi_window_specification():
    result = DrawingOfferSpecificationBuilder().build(
        extraction_fixture(),
        reviewed_positions=reviewed_fixture(),
        expected_position_numbers=(1, 2, 3, 4, 5, 6),
        review_confirmed=True,
        customer_name="Example Customer",
        language="de",
        notes="Customer supplied window drawing.",
    )

    assert result.source_alias == "drawing.jpg"
    assert result.page_number == 1
    assert result.total_quantity == 11
    assert len(result.specification.windows) == 6
    assert [
        (window.width, window.height, window.quantity)
        for window in result.specification.windows
    ] == [
        (1120, 1440, 4),
        (1100, 1440, 2),
        (700, 1440, 2),
        (2200, 1440, 1),
        (1050, 2170, 1),
        (2200, 1440, 1),
    ]
    assert result.specification.windows[0].profile == ""
    assert result.specification.windows[0].color_inside == ""

    payload = result.to_payload()
    assert payload["status"] == "human_reviewed_specification_prepared"
    assert payload["review_confirmed"] is True
    assert payload["windowhub_task_created"] is False
    assert payload["windowhub_actions_executed"] == 0
    assert payload["offer_saved"] is False
    assert payload["offer_submitted"] is False


def test_builder_rejects_unconfirmed_position_set():
    with pytest.raises(ValueError, match="explicitly confirmed"):
        DrawingOfferSpecificationBuilder().build(
            extraction_fixture(),
            reviewed_positions=reviewed_fixture(),
            expected_position_numbers=(1, 2, 3, 4, 5, 6),
            review_confirmed=False,
        )


def test_builder_rejects_position_set_that_does_not_match_ocr_candidates():
    with pytest.raises(ValueError, match="does not match"):
        DrawingOfferSpecificationBuilder().build(
            extraction_fixture(),
            reviewed_positions=reviewed_fixture(),
            expected_position_numbers=(1, 2, 3, 4, 5),
            review_confirmed=True,
        )


def test_builder_rejects_missing_reviewed_position():
    with pytest.raises(ValueError, match="exactly one reviewed"):
        DrawingOfferSpecificationBuilder().build(
            extraction_fixture(),
            reviewed_positions=reviewed_fixture()[:-1],
            expected_position_numbers=(1, 2, 3, 4, 5, 6),
            review_confirmed=True,
        )


def test_builder_rejects_any_position_without_human_confirmation():
    rows = list(reviewed_fixture())
    rows[2] = ReviewedDrawingPosition(3, 700, 1440, 2, False)

    with pytest.raises(ValueError, match="not been explicitly confirmed"):
        DrawingOfferSpecificationBuilder().build(
            extraction_fixture(),
            reviewed_positions=rows,
            expected_position_numbers=(1, 2, 3, 4, 5, 6),
            review_confirmed=True,
        )


def test_builder_rejects_invalid_dimensions_even_when_confirmed():
    rows = list(reviewed_fixture())
    rows[0] = ReviewedDrawingPosition(1, 0, 1440, 4, True)

    with pytest.raises(ValueError, match="width_mm"):
        DrawingOfferSpecificationBuilder().build(
            extraction_fixture(),
            reviewed_positions=rows,
            expected_position_numbers=(1, 2, 3, 4, 5, 6),
            review_confirmed=True,
        )


def test_builder_allows_a_human_to_correct_an_ocr_candidate():
    rows = list(reviewed_fixture())
    rows[1] = ReviewedDrawingPosition(2, 1110, 1440, 2, True)

    result = DrawingOfferSpecificationBuilder().build(
        extraction_fixture(),
        reviewed_positions=rows,
        expected_position_numbers=(1, 2, 3, 4, 5, 6),
        review_confirmed=True,
    )

    assert result.specification.windows[1].width == 1110
