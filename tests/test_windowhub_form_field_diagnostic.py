from __future__ import annotations

from types import SimpleNamespace

from tools.diagnose_windowhub_form_fields import (
    _is_field_candidate,
    _is_owned_window_candidate,
    _rank_label_candidates,
    build_field_report,
    build_semantic_field_report,
)


def test_editor_types_are_recognized_without_treating_every_button_as_a_field():
    assert _is_field_candidate("edit", "LayoutItem", "", "")
    assert _is_field_candidate("combobox", "ComboBoxEdit", "", "")
    assert _is_field_candidate("button", "LookUpEdit", "", "DevExpressButton")
    assert not _is_field_candidate("button", "Nowa oferta", "", "Button")


def test_nearby_static_text_is_ranked_ahead_of_distant_text():
    labels = [
        {"label": "Nazwa", "bounds": (60, 102, 100, 18)},
        {"label": "Odległy tekst", "bounds": (60, 240, 100, 18)},
    ]

    ranked = _rank_label_candidates((200, 100, 120, 24), labels)

    assert ranked[0]["label"] == "Nazwa"
    assert len(ranked) == 1


class _FakeRect:
    def __init__(self, left: int, top: int, width: int, height: int):
        self.left = left
        self.top = top
        self._width = width
        self._height = height

    def width(self):
        return self._width

    def height(self):
        return self._height


class _FakeItem:
    def __init__(
        self,
        *,
        name: str,
        control_type: str,
        bounds: tuple[int, int, int, int],
        value: str | None = None,
    ):
        self.element_info = SimpleNamespace(
            name=name,
            control_type=control_type,
            automation_id="",
            class_name="Fake",
            enabled=True,
            visible=True,
        )
        self._bounds = bounds
        self._value = value

    def rectangle(self):
        return _FakeRect(*self._bounds)

    def get_value(self):
        return self._value

    def parent(self):
        return None


def test_report_exposes_only_value_flags_and_redacts_window_title():
    label = _FakeItem(
        name="Nazwa",
        control_type="Text",
        bounds=(60, 102, 100, 18),
    )
    field = _FakeItem(
        name="LayoutItem",
        control_type="Edit",
        bounds=(200, 100, 120, 24),
        value="PRIVATE FIELD CONTENT",
    )

    report = build_field_report(
        [label, field],
        active_window_title="Sensitive customer window",
    )

    field_report = report["fields"][0]
    assert field_report["name"] == "LayoutItem"
    assert field_report["nearby_text_candidates"][0]["label"] == "Nazwa"
    assert field_report["value_available"] is True
    assert field_report["value_nonempty"] is True
    assert "value" not in field_report
    assert "PRIVATE FIELD CONTENT" not in str(report)
    assert report["window_title"] == "<redacted>"
    assert report["computer_actions_executed"] is False
    assert report["files_written"] is False



def test_owned_window_candidate_requires_a_distinct_window_owned_by_target_app():
    assert _is_owned_window_candidate(200, 100, 100)
    assert not _is_owned_window_candidate(100, 100, 100)
    assert not _is_owned_window_candidate(200, 100, 999)
    assert not _is_owned_window_candidate(0, 100, 100)


def test_report_includes_owned_dialog_fields_and_keeps_label_matching_local():
    app_label = _FakeItem(
        name="Toolbar text",
        control_type="Text",
        bounds=(60, 100, 100, 18),
    )
    app_field = _FakeItem(
        name="Toolbar editor",
        control_type="Edit",
        bounds=(200, 100, 120, 24),
        value="PRIVATE APPLICATION VALUE",
    )
    dialog_label = _FakeItem(
        name="Numer oferty",
        control_type="Text",
        bounds=(60, 102, 100, 18),
    )
    dialog_field = _FakeItem(
        name="LayoutItem",
        control_type="Edit",
        bounds=(200, 100, 120, 24),
        value="PRIVATE DIALOG VALUE",
    )

    report = build_field_report(
        [app_label, app_field],
        active_window_title="Sensitive customer window",
        owned_window_descendants=[[dialog_label, dialog_field]],
    )

    assert report["owned_windows_scanned"] == 1
    assert report["field_count"] == 2
    assert report["fields"][0]["window_scope"] == "application_window"
    assert report["fields"][1]["window_scope"] == "owned_window_1"
    assert report["fields"][1]["nearby_text_candidates"][0]["label"] == "Numer oferty"
    assert "PRIVATE APPLICATION VALUE" not in str(report)
    assert "PRIVATE DIALOG VALUE" not in str(report)
    assert report["computer_actions_executed"] is False
    assert report["network_calls_made"] is False
    assert report["files_written"] is False



class _FakeSemanticElement:
    def __init__(self, *, label, kind, x, y, width, height, metadata):
        self.label = label
        self.kind = kind
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.metadata = metadata


class _FakeScene:
    def __init__(self, elements):
        self.elements = elements


def test_semantic_field_report_uses_perception_roles_when_raw_uia_role_is_custom():
    label = _FakeItem(
        name="Nazwa klienta",
        control_type="Text",
        bounds=(60, 102, 100, 18),
    )
    custom_editor = _FakeItem(
        name="LayoutItem",
        control_type="Custom",
        bounds=(200, 100, 120, 24),
        value="PRIVATE RAW VALUE",
    )
    element = _FakeSemanticElement(
        label="LayoutItem",
        kind="edit",
        x=200,
        y=100,
        width=120,
        height=24,
        metadata={
            "uia_enabled": True,
            "uia_visible": True,
            "uia_runtime_id": "no-raw-match",
            "uia_window_handle": 100,
            "current_value": "PRIVATE SEMANTIC VALUE",
            "automation_id": "Field1",
        },
    )

    report = build_semantic_field_report(
        _FakeScene([element]),
        [(100, [label, custom_editor])],
        root_bounds=(0, 0, 1000, 600),
        root_handle=100,
        active_window_title="Sensitive Window",
    )

    assert report["field_count"] == 1
    field = report["fields"][0]
    assert field["kind"] == "edit"
    assert field["nearby_text_candidates"][0]["label"] == "Nazwa klienta"
    assert field["value_available"] is True
    assert field["value_nonempty"] is True
    assert "PRIVATE SEMANTIC VALUE" not in str(report)
    assert "PRIVATE RAW VALUE" not in str(report)
    assert report["computer_actions_executed"] is False


def test_semantic_field_report_does_not_match_labels_across_windows():
    app_label = _FakeItem(
        name="Klient",
        control_type="Text",
        bounds=(10, 100, 70, 18),
    )
    dialog_field = _FakeSemanticElement(
        label="LayoutItem",
        kind="edit",
        x=200,
        y=100,
        width=120,
        height=24,
        metadata={
            "uia_window_handle": 200,
            "uia_enabled": True,
            "uia_visible": True,
        },
    )

    report = build_semantic_field_report(
        _FakeScene([dialog_field]),
        [(100, [app_label])],
        root_bounds=(0, 0, 1000, 600),
        root_handle=100,
        active_window_title="WindowHub",
    )

    assert report["field_count"] == 1
    assert report["fields"][0]["nearby_text_candidates"] == []


def test_semantic_report_falls_back_to_raw_fields_for_non_foreground_owned_dialog():
    app_label = _FakeItem(
        name="Toolbar label",
        control_type="Text",
        bounds=(10, 100, 90, 18),
    )
    dialog_label = _FakeItem(
        name="Nazwa oferty",
        control_type="Text",
        bounds=(60, 102, 100, 18),
    )
    dialog_field = _FakeItem(
        name="LayoutItem",
        control_type="Custom",
        bounds=(200, 100, 120, 24),
        value="PRIVATE OFFER VALUE",
    )
    dialog_field.element_info.class_name = "DevExpress.XtraEditors.TextEdit"

    # The semantic scene represents the main app only, as when PowerShell has
    # taken foreground focus. The separately enumerated owned window still
    # contains the live UIA field and its local label candidate.
    report = build_semantic_field_report(
        _FakeScene([]),
        [(100, [app_label]), (200, [dialog_label, dialog_field])],
        root_bounds=(0, 0, 1000, 600),
        root_handle=100,
        active_window_title="WindowHub",
    )

    assert report["field_count"] == 1
    field = report["fields"][0]
    assert field["window_scope"] == "owned_window"
    assert field["source"] == "raw_uia_owned_window_fallback"
    assert field["kind"] == "custom"
    assert field["class_name"] == "DevExpress.XtraEditors.TextEdit"
    assert field["nearby_text_candidates"][0]["label"] == "Nazwa oferty"
    assert report["raw_owned_window_fallback_field_count"] == 1
    assert "PRIVATE OFFER VALUE" not in str(report)
    assert report["computer_actions_executed"] is False
    assert report["files_written"] is False


def test_semantic_owned_dialog_field_is_not_duplicated_by_raw_fallback():
    label = _FakeItem(
        name="Nazwa oferty",
        control_type="Text",
        bounds=(60, 102, 100, 18),
    )
    raw_field = _FakeItem(
        name="Nazwa",
        control_type="Edit",
        bounds=(200, 100, 120, 24),
        value="PRIVATE OFFER VALUE",
    )
    semantic_field = _FakeSemanticElement(
        label="Nazwa",
        kind="edit",
        x=200,
        y=100,
        width=120,
        height=24,
        metadata={
            "uia_window_handle": 200,
            "uia_owned_modal": True,
            "uia_enabled": True,
            "uia_visible": True,
            "current_value": "PRIVATE OFFER VALUE",
        },
    )

    report = build_semantic_field_report(
        _FakeScene([semantic_field]),
        [(100, []), (200, [label, raw_field])],
        root_bounds=(0, 0, 1000, 600),
        root_handle=100,
        active_window_title="WindowHub",
    )

    assert report["field_count"] == 1
    assert report["fields"][0]["window_scope"] == "owned_window"
    assert report["raw_owned_window_fallback_field_count"] == 0
    assert "PRIVATE OFFER VALUE" not in str(report)


def test_semantic_report_lists_unclassified_custom_controls_without_exposing_values():
    label = _FakeItem(
        name="Szerokość",
        control_type="Text",
        bounds=(40, 120, 100, 18),
    )
    custom = _FakeItem(
        name="CustomItem17",
        control_type="Custom",
        bounds=(180, 118, 140, 24),
        value="PRIVATE INPUT VALUE",
    )
    hinted_custom = _FakeItem(
        name="LayoutItem",
        control_type="Custom",
        bounds=(180, 158, 140, 24),
        value="PRIVATE SECOND VALUE",
    )
    hinted_custom.element_info.class_name = "DevExpress.XtraEditors.TextEdit"

    report = build_semantic_field_report(
        _FakeScene([]),
        [(100, [label, custom, hinted_custom])],
        root_bounds=(0, 0, 1000, 700),
        root_handle=100,
        active_window_title="WindowHub",
    )

    assert report["field_count"] == 0
    assert report["raw_control_candidate_count"] == 2
    candidates = report["raw_control_candidates"]
    assert candidates[0]["candidate_type"] == "unclassified_custom_control"
    assert candidates[0]["nearby_text_candidates"][0]["label"] == "Szerokość"
    assert candidates[1]["candidate_type"] == "editor_hint_match"
    assert candidates[1]["class_name"] == "DevExpress.XtraEditors.TextEdit"
    serialized = str(report)
    assert "PRIVATE INPUT VALUE" not in serialized
    assert "PRIVATE SECOND VALUE" not in serialized
    assert report["computer_actions_executed"] is False
    assert report["files_written"] is False


def test_raw_control_candidates_deduplicate_runtime_ids_and_prefer_owned_dialog_scope():
    control = _FakeItem(
        name="LayoutItem",
        control_type="Custom",
        bounds=(200, 100, 120, 24),
        value="PRIVATE CONTROL VALUE",
    )
    control.element_info.automation_id = "IDC_CUSTOM_EDITOR"
    control.element_info.runtime_id = (42, 7, 19)

    report = build_semantic_field_report(
        _FakeScene([]),
        [(100, [control]), (200, [control])],
        root_bounds=(0, 0, 1000, 600),
        root_handle=100,
        active_window_title="WindowHub",
    )

    candidates = report["raw_control_candidates"]
    assert report["raw_control_candidate_observed_count"] == 2
    assert report["raw_control_candidate_count"] == 1
    assert report["raw_control_candidate_duplicate_count"] == 1
    assert len(candidates) == 1
    assert candidates[0]["window_scope"] == "owned_window"
    assert candidates[0]["window_handle"] == 200
    assert candidates[0]["uia_runtime_id"] == "42-7-19"
    assert "PRIVATE CONTROL VALUE" not in str(report)
    assert report["computer_actions_executed"] is False
    assert report["files_written"] is False
