from types import SimpleNamespace

import numpy as np

from app.agent.perception.windowhub_ocr_table_parser import WindowHubOCRTableRow
from app.agent.perception.windowhub_ocr_table_refiner import refine_windowhub_ocr_table_lp


class BoxEngine:
    def __init__(self, responses):
        self.responses = list(responses)

    def __call__(self, image):
        if not self.responses:
            raise AssertionError("Unexpected OCR engine call")
        return self.responses.pop(0)


def box_for_y(center_y, *, x_min=100, y_min=202, scale=5, padding=25):
    x_center = (124 - x_min) * scale + padding
    y_center = (center_y - y_min) * scale + padding
    return np.asarray([[x_center - 5, y_center - 4], [x_center + 5, y_center - 4],
                       [x_center + 5, y_center + 4], [x_center - 5, y_center + 4]], dtype=float)


def result(items):
    return SimpleNamespace(
        txts=[text for text, _, _ in items],
        scores=[score for _, score, _ in items],
        boxes=[box_for_y(y) for _, _, y in items],
    )


def row(index, center_y, lp=None):
    return WindowHubOCRTableRow(
        row_index=index, lp=lp, lp_source="price_column_row_order" if lp is None else "ocr",
        quantity=1, article="Okno", gross_total="1045.18", gross_unit="1045.18",
        dimensions="1320 x 1345", center_y=center_y,
        missing_fields=("lp",) if lp is None else (),
    )


def test_recovers_lp_from_matching_full_column_color_and_otsu_detections():
    rows = (row(2, 238.2), row(3, 251.8))
    engine = BoxEngine([
        result([("2", 0.999, 238.2), ("3", 0.998, 251.8)]),
        result([("2", 0.999, 238.2), ("3", 0.999, 251.8)]),
    ])
    refined, reports = refine_windowhub_ocr_table_lp(rows, np.zeros((400, 200, 3), dtype=np.uint8), engine)
    assert [item.lp for item in refined] == [2, 3]
    assert all(item.lp_source == "ocr_column" for item in refined)
    assert all("lp" not in item.missing_fields for item in refined)
    assert all(report.accepted and report.reason == "unique_valid_candidate" for report in reports)


def test_conflicting_lp_detections_remain_unresolved():
    engine = BoxEngine([result([("2", 0.99, 238.2)]), result([("3", 0.99, 238.2)])])
    refined, reports = refine_windowhub_ocr_table_lp((row(2, 238.2),), np.zeros((400, 200, 3), dtype=np.uint8), engine)
    assert refined[0].lp is None
    assert "lp" in refined[0].missing_fields
    assert reports[0].accepted is False
    assert reports[0].reason == "conflicting_candidates"


def test_rejects_non_numeric_ocr_noise():
    noise = SimpleNamespace(txts=["一r"], scores=[0.99], boxes=[box_for_y(223.9)])
    engine = BoxEngine([noise, noise])
    refined, reports = refine_windowhub_ocr_table_lp((row(1, 223.9),), np.zeros((400, 200, 3), dtype=np.uint8), engine)
    assert refined[0].lp is None
    assert not reports[0].accepted
    assert reports[0].reason == "no_valid_candidate"


def test_does_not_overwrite_existing_lp_or_call_engine():
    engine = BoxEngine([])
    refined, reports = refine_windowhub_ocr_table_lp((row(2, 238.2, lp=2),), np.zeros((400, 200, 3), dtype=np.uint8), engine)
    assert refined[0].lp == 2
    assert reports == ()

def test_rejects_nonfinite_lp_confidence():
    invalid = SimpleNamespace(txts=["2"], scores=[float("nan")], boxes=[box_for_y(238.2)])
    engine = BoxEngine([invalid, invalid])
    refined, reports = refine_windowhub_ocr_table_lp(
        (row(2, 238.2),), np.zeros((400, 200, 3), dtype=np.uint8), engine
    )
    assert refined[0].lp is None
    assert "lp" in refined[0].missing_fields
    assert not reports[0].accepted
    assert reports[0].reason == "no_valid_candidate"

