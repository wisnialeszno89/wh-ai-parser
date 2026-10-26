import pytest
from types import SimpleNamespace

from tools.inspect_windowhub_ocr_table import (
    _classify_table_region_detections,
    _configure_console_output,
    _wait_for_window_foreground,
    _scan_dimensions_across_row_crops,
    _scan_lp_column_across_row_crops,
    _reasoning_handoff_audit,
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
        detection("outside vertical table region", 420, 416),
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
        detection("low area", 420, 416),
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

def test_diagnostic_scans_overlapping_high_resolution_dimension_crops():
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

    assert engine.calls == 24  # 2 rows x 4 overlapping bands x 3 variants
    assert detections == [{
        "row_index": 1,
        "x_min": 850,
        "x_max": 1350,
        "variant": "color",
        "scale": 6,
        "text": "1320x1345",
        "confidence": 0.97,
    }]
    # Row band: 20 px x scale 6 plus 40 px vertical white padding.
    assert engine.shapes[0] == (160, 3096)
    # Last image: 20 px x scale 6 and a 400 px horizontal band plus padding.
    assert engine.shapes[-1] == (160, 2496)



def test_diagnostic_scans_only_unresolved_lp_rows_without_promoting_candidates():
    import numpy as np

    class FakeEngine:
        def __init__(self):
            self.calls = 0
            self.shapes = []

        def __call__(self, image):
            self.calls += 1
            self.shapes.append(image.shape[:2])
            if self.calls == 1:
                return SimpleNamespace(txts=["1"], scores=[0.91])
            return SimpleNamespace(txts=[], scores=[])

    rows = [
        SimpleNamespace(row_index=1, center_y=30.0, lp=None),
        SimpleNamespace(row_index=2, center_y=50.0, lp=2),
    ]
    image = np.zeros((100, 300, 3), dtype=np.uint8)
    engine = FakeEngine()

    detections = _scan_lp_column_across_row_crops(rows, image, engine)

    assert engine.calls == 6  # one unresolved row x two bands x three variants
    assert detections == [{
        "row_index": 1,
        "x_min": 90,
        "x_max": 170,
        "variant": "color",
        "scale": 6,
        "text": "1",
        "confidence": 0.91,
    }]
    # Local 20px high row crop scaled 6x with 32px vertical and 72px horizontal padding.
    assert engine.shapes[0] == (152, 552)


def test_reasoning_handoff_audit_includes_table_and_excludes_screen_geometry():
    from app.agent.environment.environment_observation import EnvironmentObservation
    from app.agent.environment.environment_state import EnvironmentState
    from app.agent.perception.interaction_capability import InteractionCapability
    from app.agent.perception.windowhub_ocr_table_parser import WindowHubOCRTableRow
    from app.agent.perception.windowhub_ocr_table_pipeline import WindowHubOCRTableReconstruction

    row = WindowHubOCRTableRow(
        row_index=1,
        lp=1,
        lp_source="ocr_column",
        quantity=1,
        article="Okno",
        total_value="1045.18",
        unit_value="1045.18",
        dimensions="1320 x 1345",
        center_y=223.9,
        missing_fields=(),
    )
    reconstruction = WindowHubOCRTableReconstruction(
        rows=(row,),
        field_refinements=(),
        lp_refinements=(),
    )
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHub",
            active_window_title="Okna - OFR/4170-",
            screen_width=1920,
            screen_height=1080,
        ),
        metadata={},
    )
    elements = (
        SimpleNamespace(
            kind="text",
            label="1 Okno",
            interaction_capability=InteractionCapability.UNKNOWN,
            confidence=0.99,
            metadata={"ocr_bounds": (10, 20, 30, 8)},
        ),
    )

    audit = _reasoning_handoff_audit(observation, elements, reconstruction)

    assert audit["source"] == "WorldState.from_scene -> NaviMindTaskReasoner"
    assert audit["table_present"] is True
    assert audit["table_status"] == "complete"
    assert audit["row_count"] == 1
    assert audit["complete_row_count"] == 1
    assert audit["lp_values"] == [1]
    assert audit["lp_values_unique_and_present"] is True
    assert audit["rows_with_missing_fields"] == []
    assert audit["coordinates_excluded"] is True
    assert audit["ocr_elements_checked"] == 1
    assert audit["ocr_elements_noninteractive"] is True


def test_reasoning_handoff_audit_keeps_incomplete_rows_explicit():
    from app.agent.environment.environment_observation import EnvironmentObservation
    from app.agent.environment.environment_state import EnvironmentState
    from app.agent.perception.windowhub_ocr_table_parser import WindowHubOCRTableRow
    from app.agent.perception.windowhub_ocr_table_pipeline import WindowHubOCRTableReconstruction

    row = WindowHubOCRTableRow(
        row_index=1,
        lp=None,
        lp_source=None,
        quantity=1,
        article="Okno",
        total_value="1045.18",
        unit_value="1045.18",
        dimensions="1320 x 1345",
        center_y=223.9,
        missing_fields=("lp",),
    )
    reconstruction = WindowHubOCRTableReconstruction(
        rows=(row,),
        field_refinements=(),
        lp_refinements=(),
    )
    observation = EnvironmentObservation(
        state=EnvironmentState(
            active_application="WindowHub",
            active_window_title="Okna - OFR/4170-",
        ),
        metadata={},
    )

    audit = _reasoning_handoff_audit(observation, (), reconstruction)

    assert audit["table_present"] is True
    assert audit["table_status"] == "partial"
    assert audit["row_count"] == 1
    assert audit["complete_row_count"] == 0
    assert audit["lp_values"] == [None]
    assert audit["lp_values_unique_and_present"] is False
    assert audit["rows_with_missing_fields"] == [1]
    assert audit["coordinates_excluded"] is True
    assert audit["ocr_elements_noninteractive"] is False

@pytest.mark.parametrize("initially_focused", [False, True])
def test_inspector_retries_incomplete_offer_title_until_valid(monkeypatch, capsys, initially_focused):
    import sys
    from types import ModuleType

    import tools.inspect_windowhub_ocr_table as inspector
    from app.agent.environment.environment_observation import EnvironmentObservation
    from app.agent.environment.environment_state import EnvironmentState

    def observation(title, focused):
        return EnvironmentObservation(
            state=EnvironmentState(
                active_application="WindowHub",
                active_window_title=title,
                screen_width=1936,
                screen_height=1168,
            ),
            metadata={
                "source": "windowhub",
                "window_handle": 123,
                "foreground_window_handle": 999 if not focused else 123,
                "foreground_root_owner_handle": 999 if not focused else 123,
                "window_focused": focused,
                "screenshot": None,
            },
        )

    class FakeEnvironment:
        def __init__(self):
            if initially_focused:
                self.observations = [
                    observation("Okna -", True),
                    observation("Okna - OFR/4398-3540", True),
                ]
            else:
                self.observations = [
                    observation("Okna -", False),
                    observation("Okna -", True),
                    observation("Okna - OFR/4398-3540", True),
                ]

        def observe(self):
            return self.observations.pop(0)

    class FakeProvider:
        def perceive(self, current_observation):
            current_observation.metadata.update({
                "windowhub_ocr_status": "ok",
                "windowhub_ocr_element_count": 1,
                "windowhub_ocr_table_status": "ok",
                "windowhub_ocr_table_row_count": 1,
                "windowhub_ocr_table_complete_row_count": 1,
                "windowhub_ocr_table_field_refinement_count": 0,
                "windowhub_ocr_table_lp_refinement_count": 0,
            })
            return (detection("1 Okno", 210),)

    environment = FakeEnvironment()
    wait_handles = []

    monkeypatch.setattr(inspector, "os", SimpleNamespace(name="nt"))
    environment_module = ModuleType(
        "app.agent.environment.windowhub_environment_adapter"
    )
    environment_module.WindowHubEnvironmentAdapter = lambda: environment
    provider_module = ModuleType(
        "app.agent.perception.windowhub_ocr_provider"
    )
    provider_module.WindowHubOCRProvider = FakeProvider
    monkeypatch.setitem(
        sys.modules,
        "app.agent.environment.windowhub_environment_adapter",
        environment_module,
    )
    monkeypatch.setitem(
        sys.modules,
        "app.agent.perception.windowhub_ocr_provider",
        provider_module,
    )
    monkeypatch.setattr(
        inspector,
        "_wait_for_window_foreground",
        lambda handle: wait_handles.append(handle) or True,
    )
    monkeypatch.setattr(
        inspector,
        "_foreground_snapshot",
        lambda user32: (999, 999, "Visual Studio Code"),
    )
    monkeypatch.setattr(
        inspector.ctypes,
        "WinDLL",
        lambda *args, **kwargs: object(),
        raising=False,
    )
    monkeypatch.setattr(
        inspector,
        "_classify_table_region_detections",
        lambda elements: {},
    )
    monkeypatch.setattr(
        inspector,
        "_reasoning_handoff_audit",
        lambda observation, elements, reconstruction: {
            "table_present": True,
            "table_status": "complete",
            "row_count": 1,
            "complete_row_count": 1,
            "lp_values_unique_and_present": True,
            "rows_with_missing_fields": [],
            "coordinates_excluded": True,
            "ocr_elements_checked": len(tuple(elements)),
            "ocr_elements_noninteractive": True,
        },
    )

    result = inspector.main()
    output = capsys.readouterr().out

    assert result == 0
    assert wait_handles == ([] if initially_focused else [123])
    expected_incomplete_title_count = 1 if initially_focused else 2
    assert output.count("window_title='Okna -'") == expected_incomplete_title_count
    assert "window_title='Okna - OFR/4398-3540'" in output
    # Both fixtures include a truncated title before the complete OFR title arrives.
    assert (
        "Waiting up to 10 seconds for a focused WindowHub observation "
        "with a complete offer title."
    ) in output
    assert "ABORTED: the active WindowHub title does not identify an OFR/ offer." not in output
    assert '"table_row_count": 1' in output

def test_focus_wait_accepts_intended_offer_among_multiple_windowhub_windows(monkeypatch, capsys):
    import sys
    from types import ModuleType

    import tools.inspect_windowhub_ocr_table as inspector

    windows = (
        SimpleNamespace(
            title="Okna - Start1",
            _hWnd=111,
            left=0,
            top=0,
            width=1936,
            height=1168,
        ),
        SimpleNamespace(
            title="Okna - OFR/4402-",
            _hWnd=222,
            left=0,
            top=0,
            width=1600,
            height=1000,
        ),
    )
    pygetwindow_module = ModuleType("pygetwindow")
    pygetwindow_module.getAllWindows = lambda: windows
    monkeypatch.setitem(sys.modules, "pygetwindow", pygetwindow_module)
    monkeypatch.setattr(
        inspector.ctypes,
        "WinDLL",
        lambda *args, **kwargs: object(),
        raising=False,
    )
    monkeypatch.setattr(
        inspector,
        "_foreground_snapshot",
        lambda user32: (222, 222, "Okna - OFR/4402-"),
    )

    result = _wait_for_window_foreground(111, timeout_seconds=1.0)
    output = capsys.readouterr().out

    assert result is True
    assert "target=0xDE" in output
    assert "window_title='Okna - OFR/4402-'" in output
    assert "foreground=0xDE" in output


def test_diagnostic_includes_bottom_edge_row_but_excludes_footer():
    elements = [
        detection("15", 120, 402.5),
        detection("1 Okno", 210, 402.5),
        detection("5150x2600", 1120, 402.5),
        detection("footer total", 420, 425.0),
    ]

    result = _classify_table_region_detections(elements)

    assert [item["text"] for item in result["lp_column_ocr_detections"]] == ["15"]
    assert [item["text"] for item in result["quantity_article_ocr_detections"]] == ["1 Okno"]
    assert [item["text"] for item in result["dimensions_ocr_detections"]] == ["5150x2600"]
    assert [item["text"] for item in result["table_region_ocr_detections"]] == [
        "15", "1 Okno", "5150x2600"
    ]
    assert all(item["text"] != "footer total" for item in result["table_region_ocr_detections"])
