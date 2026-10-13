from types import SimpleNamespace

import numpy as np

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
    engine = BoxEngine([empty, empty])
    result = reconstruct_windowhub_ocr_table_rows(table_elements(), np.zeros((400, 1400, 3), dtype=np.uint8), engine)
    assert len(result.rows) == 8
    assert all(row.lp is None for row in result.rows)
    assert all("lp" in row.missing_fields for row in result.rows)
    assert all(not report.accepted and report.reason == "no_valid_candidate" for report in result.lp_refinements)


def test_pipeline_rejects_parser_override_that_could_reintroduce_partial_lp_anchors():
    engine = BoxEngine([])
    try:
        reconstruct_windowhub_ocr_table_rows([], np.zeros((400, 1400, 3), dtype=np.uint8), engine, parser_options={"anchor_x_max": 180})
    except ValueError as exc:
        assert "must not override anchor_x_max" in str(exc)
    else:
        raise AssertionError("Expected unsafe parser override to be rejected")
    assert engine.calls == 0
