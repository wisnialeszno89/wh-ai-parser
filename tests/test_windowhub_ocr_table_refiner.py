from types import SimpleNamespace

import numpy as np

from app.agent.perception.windowhub_ocr_table_parser import WindowHubOCRTableRow
from app.agent.perception.windowhub_ocr_table_refiner import refine_windowhub_ocr_table_rows


class FakeEngine:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0
        self.image_shapes = []

    def __call__(self, image):
        self.calls += 1
        self.image_shapes.append(image.shape[:2])
        if not self.responses:
            raise AssertionError("FakeEngine received an unexpected call")
        texts, scores = self.responses.pop(0)
        return SimpleNamespace(txts=texts, scores=scores)


def row(*, row_index=1, center_y=220.0, quantity=None, unit="1045.18"):
    missing = []
    if quantity is None:
        missing.append("quantity")
    if unit is None:
        missing.append("unit_value")
    return WindowHubOCRTableRow(
        row_index=row_index, lp=None, lp_source="price_column_row_order",
        quantity=quantity, article="Okno", total_value="1045.18",
        unit_value=unit, dimensions="1320 x 1345", center_y=center_y,
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


def test_recovers_split_quantity_and_article_in_row_local_bands():
    # Some OCR results split the quantity digit and article into separate
    # tokens. Each variant may combine them only inside the same row crop.
    split = response(["1", "Okno"], [0.93, 0.96])
    engine = FakeEngine([split, split, split, split, split, split])
    rows, reports = refine_windowhub_ocr_table_rows(
        [
            row(row_index=1, center_y=220.0),
            row(row_index=2, center_y=240.0),
            row(row_index=3, center_y=280.0),
        ],
        np.zeros((400, 700, 3), dtype=np.uint8),
        engine,
    )

    assert [item.quantity for item in rows] == [1, 1, 1]
    assert [report.accepted for report in reports] == [True, True, True]
    # Row bands are split at neighbouring-row midpoints; wider gaps allow
    # larger crop bands without pulling a neighbouring row into the same crop.
    assert engine.image_shapes == [
        (80, 760), (80, 760),
        (120, 760), (120, 760),
        (160, 760), (160, 760),
    ]


def test_combines_quantity_and_article_across_row_crop_variants():
    # The color pass sees only the quantity; Otsu sees only the article.
    # They are still evidence from the same isolated row crop.
    engine = FakeEngine([
        response(["1"], [0.93]),
        response(["Okno"], [0.96]),
    ])
    rows, reports = refine_windowhub_ocr_table_rows(
        [row()], np.zeros((400, 700, 3), dtype=np.uint8), engine
    )
    assert rows[0].quantity == 1
    assert "quantity" not in rows[0].missing_fields
    assert reports[0].accepted
    assert reports[0].candidate_value == 1
    assert reports[0].sources == ("color+otsu",)


def test_conflicting_standalone_quantities_across_variants_remain_unresolved():
    # Article evidence supports the row, but the two variants disagree on the
    # isolated quantity digit. Do not choose the more confident guess.
    engine = FakeEngine([
        response(["1"], [0.93]),
        response(["2", "Okno"], [0.99, 0.96]),
    ])
    rows, reports = refine_windowhub_ocr_table_rows(
        [row()], np.zeros((400, 700, 3), dtype=np.uint8), engine
    )
    assert rows[0].quantity is None
    assert "quantity" in rows[0].missing_fields
    assert not reports[0].accepted
    assert reports[0].reason == "conflicting_candidates"


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
    assert rows[0].unit_value == "793.35"
    assert "unit_value" not in rows[0].missing_fields
    assert reports[0].accepted
    assert reports[0].confidence >= 0.99


def test_conflicting_unit_prices_remain_unresolved():
    engine = FakeEngine([response(["793,35"], [0.96]), response(["793,36"], [0.99])])
    rows, reports = refine_windowhub_ocr_table_rows([row(quantity=1, unit=None)], np.zeros((400, 700, 3), dtype=np.uint8), engine)
    assert rows[0].unit_value is None
    assert "unit_value" in rows[0].missing_fields
    assert not reports[0].accepted
    assert reports[0].reason == "conflicting_candidates"


def test_never_overwrites_fields_already_present():
    engine = FakeEngine([])
    rows, reports = refine_windowhub_ocr_table_rows([row(quantity=1, unit="1045.18")], np.zeros((400, 700, 3), dtype=np.uint8), engine)
    assert rows[0].quantity == 1
    assert rows[0].unit_value == "1045.18"
    assert reports == ()
    assert engine.calls == 0

def test_rejects_nonfinite_quantity_confidence():
    engine = FakeEngine([response(["1 Okno"], [float("nan")]), response(["1 Okno"], [float("nan")])])
    rows, reports = refine_windowhub_ocr_table_rows([row()], np.zeros((400, 700, 3), dtype=np.uint8), engine)
    assert rows[0].quantity is None
    assert "quantity" in rows[0].missing_fields
    assert not reports[0].accepted
    assert reports[0].reason == "no_valid_candidate"

