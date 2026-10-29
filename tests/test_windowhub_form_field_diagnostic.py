from __future__ import annotations

from types import SimpleNamespace

from tools.diagnose_windowhub_form_fields import (
    _is_field_candidate,
    _is_owned_window_candidate,
    _rank_label_candidates,
    build_field_report,
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
