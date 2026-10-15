from types import SimpleNamespace

from tools.inspect_windowhub_ocr_table import (
    _classify_table_region_detections,
    _configure_console_output,
    _scan_dimensions_across_row_crops,
)


def detection(text, x, center_y=220.0, *, confidence=0.99):
    return SimpleNamespace(
        label=text,
        x=x,
        y=center_y - 4,
        width=max(8, len(text) * 7),
        height=8,
        confidence=confidence,
    )


def test_diagnostic_preserves_raw_detections_for_each_table_column():
    elements = [
        detection("4", 120),
        detection("2 Okno", 210),
        detection("1045,18", 420),
        detection("522,59", 530),
        detection("1320x1345", 1120),
        detection("irrelevant UI label", 800),
        detection("outside vertical table region", 420, 390),
    ]

    result = _classify_table_region_detections(elements)

    assert [item["text"] for item in result["lp_column_ocr_detections"]] == ["4"]
    assert [item["text"] for item in result["quantity_article_ocr_detections"]] == ["2 Okno"]
    assert [item["text"] for item in result["total_value_ocr_detections"]] == ["1045,18"]
    assert [item["text"] for item in result["unit_value_ocr_detections"]] == ["522,59"]
    assert [item["text"] for item in result["dimensions_ocr_detections"]] == ["1320x1345"]
    assert len(result["table_region_ocr_detections"]) == 5


def test_diagnostic_skips_malformed_and_invalid_detections():
    elements = [
        object(),
        SimpleNamespace(label="invalid", x=None, y=200, width=20, height=8, confidence=0.9),
        detection("low area", 420, 380),
        detection("outside x", 700, 220),
    ]

    result = _classify_table_region_detections(elements)

    assert result["table_region_ocr_detections"] == []
    assert result["total_value_ocr_detections"] == []

def test_console_output_uses_backslash_replacement_for_legacy_code_pages():
    class Stream:
        def __init__(self):
            self.options = []

        def reconfigure(self, **kwargs):
            self.options.append(kwargs)

    stdout = Stream()
    stderr = Stream()

    _configure_console_output((stdout, stderr))

    assert stdout.options == [{"errors": "backslashreplace"}]
    assert stderr.options == [{"errors": "backslashreplace"}]


def test_diagnostic_infers_shifted_price_columns_and_excludes_montage_from_unit_value():
    elements = [
        detection("1 Okno", 210),
        detection("1045,18", 365),
        detection("793,35", 464),
        detection("0,00", 551),
        detection("Montaż brutto", 521),
        detection("1320x1345", 1280),
        detection("1045,18", 365, 237),
        detection("793,35", 464, 237),
        detection("0,00", 551, 237),
    ]

    result = _classify_table_region_detections(elements)

    assert "1045,18" in [item["text"] for item in result["total_value_ocr_detections"]]
    assert "793,35" in [item["text"] for item in result["unit_value_ocr_detections"]]
    assert "0,00" in [item["text"] for item in result["other_price_column_ocr_detections"]]
    assert "1045,18" not in [item["text"] for item in result["quantity_article_ocr_detections"]]
    assert [item["text"] for item in result["dimensions_ocr_detections"]] == ["1320x1345"]

def test_diagnostic_scans_right_side_crop_bands_per_row():
    import numpy as np

    class FakeEngine:
        def __init__(self):
            self.calls = 0
            self.shapes = []

        def __call__(self, image):
            self.calls += 1
            self.shapes.append(image.shape[:2])
            if self.calls == 1:
                return SimpleNamespace(txts=["1320x1345"], scores=[0.97])
            return SimpleNamespace(txts=[], scores=[])

    rows = [
        SimpleNamespace(row_index=1, center_y=30.0),
        SimpleNamespace(row_index=2, center_y=50.0),
    ]
    image = np.zeros((100, 1936, 3), dtype=np.uint8)
    engine = FakeEngine()

    detections = _scan_dimensions_across_row_crops(rows, image, engine)

    assert engine.calls == 16  # 2 rows x 4 horizontal bands x 2 variants
    assert detections == [{
        "row_index": 1,
        "x_min": 650,
        "x_max": 1000,
        "variant": "color",
        "text": "1320x1345",
        "confidence": 0.97,
    }]
    assert engine.shapes[0] == (80, 1400)
    assert engine.shapes[-1] == (80, 944)
