from __future__ import annotations

from app.agent.adapters.document_ocr import OCRTextRegion
from app.agent.adapters.pdf_document_adapter import PdfPageFinding
from app.agent.offers.drawing_position_extractor import DrawingPositionExtractor


def box(
    text: str,
    x: int,
    y: int,
    width: int,
    height: int,
    confidence: float = 0.99,
) -> OCRTextRegion:
    return OCRTextRegion(
        text=text,
        confidence=confidence,
        x=x,
        y=y,
        width=width,
        height=height,
    )


def page_with_regions(regions: list[OCRTextRegion]) -> PdfPageFinding:
    return PdfPageFinding(
        source_alias="drawing-test.jpg",
        page_number=1,
        text="",
        extraction_method="rapidocr_image",
        extraction_confidence=0.993,
        needs_ocr=False,
        limitations=(),
        ocr_regions=tuple(regions),
    )


def conradi_six_position_regions() -> list[OCRTextRegion]:
    """Boxes sampled from the real six-position Conradi drawing OCR output."""
    regions = [
        # First row: three Position/Menge headings.
        box("Position 1", 113, 94, 118, 48),
        box("Menge 4", 297, 120, 104, 46),
        box("Position 2", 525, 144, 110, 36),
        box("Menge 2", 744, 153, 98, 37),
        box("Position 3", 938, 159, 108, 32),
        box("Menge 2", 1146, 162, 99, 35),
        # First row: inner height/outer height/overall width labels.
        box("+210-", 157, 198, 30, 68),
        box("1200", 154, 371, 30, 58),
        box("1440", 455, 376, 31, 60),
        box("1120", 289, 563, 61, 36),
        box("+210+", 585, 237, 31, 65),
        box("1200", 582, 404, 31, 57),
        box("1440", 872, 394, 28, 51),
        box("1100", 710, 584, 58, 33),
        box("+210+", 1046, 249, 32, 66),
        box("1200", 1041, 416, 34, 55),
        box("1440", 1243, 401, 28, 51),
        box("700", 1131, 593, 46, 29),
        # Second row: position headers and quantities.
        box("Position 4", 105, 629, 117, 40),
        box("Menge 1", 291, 644, 100, 37),
        box("Position 5", 517, 657, 108, 31),
        box("Menge 1", 735, 662, 95, 33),
        box("Position 6", 928, 666, 107, 29),
        box("Menge 1", 1135, 667, 98, 36),
        # Second row dimensions. 2200 is the overall width over two 1100 leaves.
        box("2200", 285, 785, 62, 33),
        box("1200", 120, 900, 30, 57),
        box("1440", 475, 902, 28, 54),
        box("1100", 206, 1025, 56, 30),
        box("1100", 362, 1028, 59, 33),
        box("2170", 811, 896, 34, 60),
        box("1930", 620, 907, 31, 57),
        box("1050", 702, 1091, 55, 27),
        box("2200", 1121, 806, 57, 32),
        box("1200", 960, 920, 31, 58),
        box("1440", 1307, 917, 28, 54),
        box("1100", 1041, 1043, 55, 28),
        box("1100", 1196, 1046, 54, 28),
    ]
    return regions


def test_six_window_positions_extract_outer_dimensions_and_quantities():
    result = DrawingPositionExtractor().extract(
        page_with_regions(conradi_six_position_regions())
    )

    assert result.complete is True
    assert result.requires_visual_review is True
    assert result.issues == ()
    assert [
        (
            item.position_number,
            item.quantity,
            item.width_mm,
            item.height_mm,
        )
        for item in result.positions
    ] == [
        (1, 4, 1120, 1440),
        (2, 2, 1100, 1440),
        (3, 2, 700, 1440),
        (4, 1, 2200, 1440),
        (5, 1, 1050, 2170),
        (6, 1, 2200, 1440),
    ]
    assert sum(item.quantity or 0 for item in result.positions) == 11
    assert all(item.confidence is not None for item in result.positions)
    assert all(item.to_payload()["requires_visual_review"] is True for item in result.positions)


def test_drawing_extractor_does_not_guess_when_dimensions_are_missing():
    page = page_with_regions([
        box("Position 1", 10, 10, 100, 30),
        box("Menge 2", 140, 10, 80, 30),
        box("1200", 20, 120, 60, 25),
    ])

    result = DrawingPositionExtractor().extract(page)

    assert result.requires_visual_review is True
    assert len(result.positions) == 1
    assert result.positions[0].quantity == 2
    assert result.positions[0].width_mm == 1200
    assert result.positions[0].height_mm is None
    assert result.positions[0].complete is False
    assert "overall_height_not_found" in result.positions[0].issues
    assert "one_or_more_positions_need_manual_field_review" in result.issues


def test_drawing_extractor_requires_explicit_position_headers():
    page = page_with_regions([
        box("1200", 20, 120, 60, 25),
        box("1440", 200, 120, 30, 60),
    ])

    result = DrawingPositionExtractor().extract(page)

    assert result.positions == ()
    assert result.complete is False
    assert result.issues == ("no_explicit_position_labels_found",)
