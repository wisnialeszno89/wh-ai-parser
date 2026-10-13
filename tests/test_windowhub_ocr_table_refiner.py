from types import SimpleNamespace

import numpy as np

from app.agent.perception.windowhub_ocr_table_parser import WindowHubOCRTableRow
from app.agent.perception.windowhub_ocr_table_refiner import refine_windowhub_ocr_table_rows


class FakeEngine:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def __call__(self, image):
        self.calls += 1
        if not self.responses:
            raise AssertionError("FakeEngine received an unexpected call")
        texts, scores = self.responses.pop(0)
        return SimpleNamespace(txts=texts, scores=scores)


def row(*, quantity=None, unit="1045.18"):
    missing = []
    if quantity is None:
        missing.append("quantity")
    if unit is None:
        missing.append("gross_unit")
    return WindowHubOCRTableRow(
        row_index=1, lp=None, lp_source="price_column_row_order",
        quantity=quantity, article="Okno", gross_total="1045.18",
        gross_unit=unit, dimensions="1320 x 1345", center_y=220.0,
        missing_fields=tuple(missing),
    )


def response(texts, scores):
    return texts, scores


def test_recovers_quantity_when_article_matches_in_both_variants():
    engine = FakeEngine([response(["1 Okno"], [0.91]), response(["1 Okno"], [0.93])])
    rows, reports = refine_windowhub_ocr_table_rows([row()], np.zeros((400, 700, 3), dtype=np.uint8), engine)
    assert rows[0].quantity == 1
    assert "quantity" not in rows[0].missing_fields
    assert reports[0].accepted
    assert reports[0].candidate_value == 1


def test_rejects_false_quantity_when_article_does_not_match():
    engine = FakeEngine([response(["10kno"], [0.92]), response(["10kno"], [0.92])])
    rows, reports = refine_windowhub_ocr_table_rows([row()], np.zeros((400, 700, 3), dtype=np.uint8), engine)
    assert rows[0].quantity is None
    assert "quantity" in rows[0].missing_fields
    assert not reports[0].accepted
    assert reports[0].reason == "no_valid_candidate"


def test_accepts_valid_color_candidate_when_otsu_has_article_typo():
    engine = FakeEngine([response(["1 Okno"], [0.92]), response(["10kno"], [0.92])])
    rows, reports = refine_windowhub_ocr_table_rows([row()], np.zeros((400, 700, 3), dtype=np.uint8), engine)
    assert rows[0].quantity == 1
    assert reports[0].accepted
    assert reports[0].candidate_value == 1


def test_recovers_missing_unit_price_from_otsu_result():
    engine = FakeEngine([response([], []), response(["793,35"], [0.996])])
    rows, reports = refine_windowhub_ocr_table_rows([row(quantity=1, unit=None)], np.zeros((400, 700, 3), dtype=np.uint8), engine)
    assert rows[0].gross_unit == "793.35"
    assert "gross_unit" not in rows[0].missing_fields
    assert reports[0].accepted
    assert reports[0].confidence >= 0.99


def test_conflicting_unit_prices_remain_unresolved():
    engine = FakeEngine([response(["793,35"], [0.96]), response(["793,36"], [0.99])])
    rows, reports = refine_windowhub_ocr_table_rows([row(quantity=1, unit=None)], np.zeros((400, 700, 3), dtype=np.uint8), engine)
    assert rows[0].gross_unit is None
    assert "gross_unit" in rows[0].missing_fields
    assert not reports[0].accepted
    assert reports[0].reason == "conflicting_candidates"


def test_never_overwrites_fields_already_present():
    engine = FakeEngine([])
    rows, reports = refine_windowhub_ocr_table_rows([row(quantity=1, unit="1045.18")], np.zeros((400, 700, 3), dtype=np.uint8), engine)
    assert rows[0].quantity == 1
    assert rows[0].gross_unit == "1045.18"
    assert reports == ()
    assert engine.calls == 0
