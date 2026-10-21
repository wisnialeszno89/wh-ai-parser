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
        quantity=1, article="Okno", total_value="1045.18", unit_value="1045.18",
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

def test_row_local_consensus_resolves_conflicting_full_column_reads():
    empty = SimpleNamespace(txts=[], scores=[], boxes=[])
    observed_six = SimpleNamespace(txts=["6"], scores=[0.9995])
    engine = BoxEngine([
        # Two full-column variants disagree for this physical row.
        result([("6", 0.999, 238.2)]),
        result([("8", 0.998, 238.2)]),
        # The high-resolution row-local crops agree on LP 6.
        empty, empty, observed_six,
        empty, empty, observed_six,
    ])

    refined, reports = refine_windowhub_ocr_table_lp(
        (row(2, 238.2),),
        np.zeros((400, 200, 3), dtype=np.uint8),
        engine,
    )

    assert refined[0].lp == 6
    assert refined[0].lp_source == "ocr_cell"
    assert "lp" not in refined[0].missing_fields
    assert reports[0].accepted is True
    assert reports[0].candidate_value == 6
    assert reports[0].reason == "unique_valid_candidate"
    assert reports[0].sources == (
        "cell_x100_180:otsu_sharpened",
        "cell_x90_170:otsu_sharpened",
    )


def test_rejects_non_numeric_ocr_noise():
    noise = SimpleNamespace(txts=["一r"], scores=[0.99], boxes=[box_for_y(223.9)])
    engine = BoxEngine([noise, noise, noise, noise, noise, noise, noise, noise])
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
    engine = BoxEngine([invalid, invalid, invalid, invalid, invalid, invalid, invalid, invalid])
    refined, reports = refine_windowhub_ocr_table_lp(
        (row(2, 238.2),), np.zeros((400, 200, 3), dtype=np.uint8), engine
    )
    assert refined[0].lp is None
    assert "lp" in refined[0].missing_fields
    assert not reports[0].accepted
    assert reports[0].reason == "no_valid_candidate"



def test_recovers_lp_for_last_row_near_parser_vertical_limit():
    rows = (row(10, 345.0),)
    engine = BoxEngine([
        result([("21", 0.999, 345.0)]),
        result([("21", 0.999, 345.0)]),
    ])
    refined, reports = refine_windowhub_ocr_table_lp(
        rows, np.zeros((400, 200, 3), dtype=np.uint8), engine
    )
    assert refined[0].lp == 21
    assert refined[0].lp_source == "ocr_column"
    assert "lp" not in refined[0].missing_fields
    assert reports[0].accepted
    assert reports[0].reason == "unique_valid_candidate"


def test_rejects_duplicate_lp_candidates_across_rows():
    rows = (row(3, 238.2), row(4, 251.8))
    engine = BoxEngine([
        result([("6", 0.999, 238.2), ("6", 0.999, 251.8)]),
        result([("6", 0.999, 238.2), ("6", 0.999, 251.8)]),
    ])
    refined, reports = refine_windowhub_ocr_table_lp(
        rows, np.zeros((400, 200, 3), dtype=np.uint8), engine
    )
    assert [item.lp for item in refined] == [None, None]
    assert all("lp" in item.missing_fields for item in refined)
    assert [report.candidate_value for report in reports] == [6, 6]
    assert all(not report.accepted for report in reports)
    assert all(report.reason == "duplicate_lp_across_rows" for report in reports)


def test_rejects_lp_candidate_matching_an_existing_row_lp():
    rows = (row(1, 223.9, lp=6), row(2, 238.2))
    engine = BoxEngine([
        result([("6", 0.999, 238.2)]),
        result([("6", 0.999, 238.2)]),
    ])
    refined, reports = refine_windowhub_ocr_table_lp(
        rows, np.zeros((400, 200, 3), dtype=np.uint8), engine
    )
    assert refined[0].lp == 6
    assert refined[1].lp is None
    assert "lp" in refined[1].missing_fields
    assert reports[0].candidate_value == 6
    assert not reports[0].accepted
    assert reports[0].reason == "duplicate_lp_existing_row"


def test_preserves_lp_when_multiple_rows_share_the_same_candidate():
    rows = (row(3, 238.2), row(4, 251.8))
    engine = BoxEngine([
        result([("6", 0.999, 238.2), ("6", 0.999, 251.8)]),
        result([("6", 0.999, 238.2), ("6", 0.999, 251.8)]),
    ])
    refined, reports = refine_windowhub_ocr_table_lp(
        rows, np.zeros((400, 200, 3), dtype=np.uint8), engine
    )
    assert [item.lp for item in refined] == [None, None]
    assert all("lp" in item.missing_fields for item in refined)
    assert all(not report.accepted for report in reports)
    assert all(report.reason == "duplicate_lp_across_rows" for report in reports)


def test_preserves_lp_when_candidate_duplicates_existing_row():
    rows = (row(1, 223.9, lp=6), row(2, 238.2))
    engine = BoxEngine([
        result([("6", 0.999, 238.2)]),
        result([("6", 0.999, 238.2)]),
    ])
    refined, reports = refine_windowhub_ocr_table_lp(
        rows, np.zeros((400, 200, 3), dtype=np.uint8), engine
    )
    assert refined[0].lp == 6
    assert refined[1].lp is None
    assert "lp" in refined[1].missing_fields
    assert not reports[0].accepted
    assert reports[0].reason == "duplicate_lp_existing_row"



def test_recovers_lp_from_high_confidence_row_local_cell_crop():
    empty = SimpleNamespace(txts=[], scores=[], boxes=[])
    observed_one = SimpleNamespace(txts=["1"], scores=[0.9985])
    engine = BoxEngine([
        empty, empty,       # legacy full-column color / Otsu attempts
        empty, empty,       # first cell band: color / CLAHE
        observed_one,       # first cell band: Otsu-sharpened reads LP 1
        empty, empty, empty # second overlapping cell band
    ])

    refined, reports = refine_windowhub_ocr_table_lp(
        (row(1, 223.9),), np.zeros((400, 200, 3), dtype=np.uint8), engine
    )

    assert refined[0].lp == 1
    assert refined[0].lp_source == "ocr_cell"
    assert "lp" not in refined[0].missing_fields
    assert reports[0].accepted
    assert reports[0].candidate_value == 1
    assert reports[0].reason == "unique_valid_candidate"
    assert reports[0].sources == ("cell_x90_170:otsu_sharpened",)


def test_conflicting_row_local_lp_candidates_remain_unresolved():
    empty = SimpleNamespace(txts=[], scores=[], boxes=[])
    observed_one = SimpleNamespace(txts=["1"], scores=[0.9985])
    observed_seven = SimpleNamespace(txts=["7"], scores=[0.992])
    engine = BoxEngine([
        empty, empty,       # legacy full-column attempts
        empty, empty, observed_one,  # band 90..170
        empty, empty, observed_seven # band 100..180
    ])

    refined, reports = refine_windowhub_ocr_table_lp(
        (row(1, 223.9),), np.zeros((400, 200, 3), dtype=np.uint8), engine
    )

    assert refined[0].lp is None
    assert "lp" in refined[0].missing_fields
    assert not reports[0].accepted
    assert reports[0].reason == "conflicting_candidates"
    assert reports[0].candidate_value is None
