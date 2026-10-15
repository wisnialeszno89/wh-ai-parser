from types import SimpleNamespace

import numpy as np

from app.agent.perception.windowhub_ocr_table_parser import infer_windowhub_ocr_table_column_layout
from app.agent.perception.windowhub_ocr_table_pipeline import reconstruct_windowhub_ocr_table_rows


CENTERS = (223.9, 238.2, 251.8, 266.1, 280.4, 294.0, 308.0, 322.0)


class BoxEngine:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def __call__(self, image):
        self.calls += 1
        if not self.responses:
            raise AssertionError("Unexpected OCR engine call")
        return self.responses.pop(0)


def ocr_result(pairs):
    texts, scores, boxes = [], [], []
    for text, confidence, center_y in pairs:
        texts.append(text)
        scores.append(confidence)
        x_center = (124 - 100) * 5 + 25
        y_center = (center_y - 202) * 5 + 25
        boxes.append(np.asarray([[x_center - 5, y_center - 4], [x_center + 5, y_center - 4],
                                 [x_center + 5, y_center + 4], [x_center - 5, y_center + 4]], dtype=float))
    return SimpleNamespace(txts=texts, scores=scores, boxes=boxes)


def element(label, x, center_y, confidence=0.99):
    return SimpleNamespace(label=label, x=x, y=center_y - 4, width=max(8, len(label) * 7), height=8, confidence=confidence)


def table_elements(include_partial_lp=True):
    elements = []
    visible_lp = {2, 3, 5, 6, 7, 8} if include_partial_lp else set()
    for number, center_y in enumerate(CENTERS, start=1):
        elements.extend([element("1 Okno", 210, center_y), element("1045,18", 420, center_y),
                         element("1045,18", 530, center_y), element("1320x1345", 1120, center_y)])
        if number in visible_lp:
            elements.append(element(str(number), 120, center_y))
    return elements


def test_pipeline_keeps_all_rows_when_full_image_lp_ocr_is_partial():
    full_lp = [(str(n), 0.999, center_y) for n, center_y in enumerate(CENTERS, 1)]
    engine = BoxEngine([ocr_result(full_lp), ocr_result(full_lp)])
    result = reconstruct_windowhub_ocr_table_rows(table_elements(), np.zeros((400, 1400, 3), dtype=np.uint8), engine)
    assert len(result.rows) == 8
    assert [row.lp for row in result.rows] == list(range(1, 9))
    assert all(row.lp_source == "ocr_column" for row in result.rows)
    assert all("lp" not in row.missing_fields for row in result.rows)
    assert result.field_refinements == ()
    assert len(result.lp_refinements) == 8
    assert all(report.accepted for report in result.lp_refinements)
    assert engine.calls == 2


def test_pipeline_does_not_guess_lp_when_column_ocr_has_no_valid_digits():
    empty = SimpleNamespace(txts=[], scores=[], boxes=[])

    class AlwaysEmptyEngine:
        def __init__(self):
            self.calls = 0

        def __call__(self, image):
            self.calls += 1
            return empty

    engine = AlwaysEmptyEngine()
    result = reconstruct_windowhub_ocr_table_rows(table_elements(), np.zeros((400, 1400, 3), dtype=np.uint8), engine)
    assert len(result.rows) == 8
    assert all(row.lp is None for row in result.rows)
    assert all("lp" in row.missing_fields for row in result.rows)
    assert all(not report.accepted and report.reason == "no_valid_candidate" for report in result.lp_refinements)
    assert engine.calls == 2 + 8 * 6  # full-column scan plus six LP-cell variants per unresolved row


def test_pipeline_rejects_parser_override_that_could_reintroduce_partial_lp_anchors():
    engine = BoxEngine([])
    try:
        reconstruct_windowhub_ocr_table_rows([], np.zeros((400, 1400, 3), dtype=np.uint8), engine, parser_options={"anchor_x_max": 180})
    except ValueError as exc:
        assert "must not override anchor_x_max" in str(exc)
    else:
        raise AssertionError("Expected unsafe parser override to be rejected")
    assert engine.calls == 0


def test_pipeline_uses_shifted_article_crop_and_never_promotes_montage_to_unit_value():
    class RecordingEmptyEngine:
        def __init__(self):
            self.widths = []

        def __call__(self, image):
            self.widths.append(image.shape[1])
            return SimpleNamespace(txts=[], scores=[], boxes=[])

    items = []
    for lp, center_y in ((1, 224.0), (2, 241.0)):
        items.extend([
            element("1 Okno" if lp == 1 else "Okno", 210, center_y),
            element(f"{1000 + lp},00", 365, center_y),
            element(f"{800 + lp},00", 464, center_y),
            element("0,00", 551, center_y),
            element("1320x1345", 1120, center_y),
            element(str(lp), 120, center_y),
        ])
    engine = RecordingEmptyEngine()
    result = reconstruct_windowhub_ocr_table_rows(
        items, np.zeros((400, 1400, 3), dtype=np.uint8), engine
    )

    assert [row.total_value for row in result.rows] == ["1001.00", "1002.00"]
    assert [row.unit_value for row in result.rows] == ["801.00", "802.00"]
    assert [row.article for row in result.rows] == ["Okno", "Okno"]
    assert result.rows[0].quantity == 1
    assert result.rows[1].quantity is None
    layout = infer_windowhub_ocr_table_column_layout(items)
    centers = layout["price_column_centers"]
    assert layout["adaptive_price_columns"] is True
    assert len(centers) == 3
    assert layout["article_x_max"] == int(centers[0] - 38)
    assert layout["unit_x_min"] < centers[1] < layout["unit_x_max"] < centers[2]
    # The OCR engine receives scaled crops. The dynamic article crop width
    # must match its inferred boundary, while the later Montage column stays out.
    expected_article_crop_width = (int(layout["article_x_max"]) - 190) * 4
    assert engine.widths.count(expected_article_crop_width) == 2

def test_pipeline_passes_dimensions_column_to_local_refiner():
    class RecordingDimensionEngine:
        def __init__(self):
            self.image_shapes = []

        def __call__(self, image):
            self.image_shapes.append(image.shape[:2])
            return SimpleNamespace(txts=["1320x1345"], scores=[0.97])

    items = [
        element("1 Okno", 210, 224.0),
        element("1045,18", 365, 224.0),
        element("793,35", 464, 224.0),
        element("0,00", 551, 224.0),
        element("1", 120, 224.0),
    ]
    engine = RecordingDimensionEngine()
    result = reconstruct_windowhub_ocr_table_rows(
        items,
        np.zeros((400, 1800, 3), dtype=np.uint8),
        engine,
        parser_options={"dimensions_x_min": 1200, "dimensions_x_max": 1500},
    )
    assert len(result.rows) == 1
    assert result.rows[0].dimensions == "1320 x 1345"
    assert any(report.field == "dimensions" and report.accepted for report in result.field_refinements)
    # Three padded, high-resolution passes share the configured dimension crop.
    assert engine.image_shapes.count((148, 1896)) == 3



def test_pipeline_uses_header_labels_for_single_row_and_excludes_montage_price():
    items = [
        element("Lp", 135, 191.0),
        element("Ilość", 179, 189.0),
        element("Artykuł", 257, 190.0),
        element("Wartość", 350, 190.0),
        element("Wartość (szt.)", 419, 199.0),
        element("Montaż", 521, 193.0),
        element("1 Okno", 205, 224.0),
        element("3944,33", 364, 224.0),
        element("3944,33", 463, 224.0),
        element("0,00", 548, 224.0),
        element("2580 Î 2240", 975, 224.0),
    ]

    class EmptyEngine:
        def __call__(self, image):
            return SimpleNamespace(txts=[], scores=[], boxes=[])

    engine = EmptyEngine()
    result = reconstruct_windowhub_ocr_table_rows(
        items, np.zeros((400, 1800, 3), dtype=np.uint8), engine
    )

    assert len(result.rows) == 1
    row = result.rows[0]
    assert row.lp is None
    assert row.quantity == 1
    assert row.article == "Okno"
    assert row.total_value == "3944.33"
    assert row.unit_value == "3944.33"
    assert row.unit_value != "0.00"
    assert row.dimensions == "2580 x 2240"
    assert "lp" in row.missing_fields

    layout = infer_windowhub_ocr_table_column_layout(items)
    assert layout["adaptive_price_columns"] is True
    assert layout["price_column_source"] == "header_text"
    assert len(layout["price_column_centers"]) == 3
