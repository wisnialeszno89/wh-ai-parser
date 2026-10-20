from types import SimpleNamespace

from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)
from tools.diagnose_windowhub_field_scope import (
    _scene_field_element_census,
    _summarize_uia_field_candidates,
    _uia_nonstandard_candidate_summary,
)


class FakeUIAItem:
    def __init__(
        self,
        *,
        name,
        control_type,
        left,
        top,
        width,
        height,
        visible=True,
        handle=None,
        parent=None,
        class_name="",
        automation_id="",
    ):
        self.element_info = SimpleNamespace(
            name=name,
            control_type=control_type,
            visible=visible,
            enabled=True,
            handle=handle,
            class_name=class_name,
            automation_id=automation_id,
        )
        self._rectangle = SimpleNamespace(
            left=left,
            top=top,
            width=lambda: width,
            height=lambda: height,
        )
        self._parent = parent

    def rectangle(self):
        return self._rectangle

    def parent(self):
        return self._parent


def test_raw_uia_field_census_counts_pipeline_stages_without_private_text():
    label = FakeUIAItem(
        name="SENSITIVE_LABEL_SHOULD_NOT_LEAK",
        control_type="Text",
        left=10,
        top=100,
        width=75,
        height=18,
    )
    editor = FakeUIAItem(
        name="LayoutItem",
        control_type="Edit",
        left=90,
        top=100,
        width=100,
        height=20,
        handle=501,
    )
    combo = FakeUIAItem(
        name="SECRET_COMBO_TITLE_SHOULD_NOT_LEAK",
        control_type="ComboBox",
        left=90,
        top=150,
        width=100,
        height=20,
        handle=502,
    )
    hidden_editor = FakeUIAItem(
        name="SECRET_HIDDEN_TITLE_SHOULD_NOT_LEAK",
        control_type="Edit",
        left=90,
        top=200,
        width=100,
        height=20,
        visible=False,
        handle=503,
    )
    descendants = (label, editor, combo, hidden_editor)
    provider = WindowHubUIAutomationProvider()
    label_candidates = provider._collect_label_candidates(
        descendants,
        origin_x=0,
        origin_y=0,
    )

    result = _summarize_uia_field_candidates(
        descendants,
        provider=provider,
        origin_x=0,
        origin_y=0,
        label_candidates=label_candidates,
    )

    assert result["available"] is True
    assert result["descendant_count"] == 4
    assert result["control_type_counts"]["edit"] == 2
    assert result["control_type_counts"]["combobox"] == 1
    assert result["control_type_counts"]["text"] == 1
    assert result["field_control_count"] == 3
    assert result["field_control_visible_count"] == 2
    assert result["field_control_visible_with_positive_bounds_count"] == 2
    assert result["field_control_visible_with_direct_name_count"] == 2
    assert result["field_control_visible_with_semantic_label_count"] == 2
    assert (
        result[
            "field_control_visible_with_positive_bounds_and_semantic_label_count"
        ]
        == 2
    )
    assert result["field_control_native_handle_present_count"] == 3
    assert result["field_control_metadata_read_failure_count"] == 0

    rendered = repr(result)
    for private_text in (
        "SENSITIVE_LABEL_SHOULD_NOT_LEAK",
        "SECRET_COMBO_TITLE_SHOULD_NOT_LEAK",
        "SECRET_HIDDEN_TITLE_SHOULD_NOT_LEAK",
        "LayoutItem",
        "501",
        "502",
        "503",
    ):
        assert private_text not in rendered


def test_scene_field_census_separates_uia_field_controls_from_other_sources():
    elements = (
        ScreenElement(
            kind="edit",
            label="field",
            metadata={"source": "windowhub_ui_automation"},
        ),
        ScreenElement(
            kind="combobox",
            label="field",
            metadata={"source": "windowhub_ui_automation"},
        ),
        ScreenElement(
            kind="edit",
            label="field",
            metadata={"source": "windowhub_vision_pipeline"},
        ),
        ScreenElement(kind="tabitem", label="OFR", metadata={}),
    )

    result = _scene_field_element_census(elements)

    assert result == {
        "edit_count": 2,
        "combobox_count": 1,
        "ui_automation_edit_count": 1,
        "ui_automation_combobox_count": 1,
        "scene_field_control_count": 3,
        "ui_automation_field_control_count": 2,
    }



def test_nonstandard_uia_census_counts_value_patterns_without_emitting_text():
    winforms_custom = FakeUIAItem(
        name="SENSITIVE_CUSTOM_NAME",
        control_type="Custom",
        left=10,
        top=100,
        width=100,
        height=24,
        handle=501,
        class_name="WindowsForms10.Window.8.app.0",
        automation_id="SECRET_AUTOMATION_ID",
    )
    winforms_custom.iface_value = object()
    winforms_custom.iface_text = object()

    mfc_other = FakeUIAItem(
        name="SENSITIVE_OTHER_NAME",
        control_type="Other",
        left=20,
        top=140,
        width=100,
        height=24,
        handle=502,
        class_name="Afx:Wnd42",
        automation_id="SECRET_OTHER_ID",
    )
    mfc_other.iface_legacy_iaccessible = object()
    mfc_other.iface_value = object()

    no_pattern = FakeUIAItem(
        name="SENSITIVE_EMPTY_NAME",
        control_type="Custom",
        left=30,
        top=180,
        width=0,
        height=0,
        handle=None,
        class_name="",
    )

    result = _uia_nonstandard_candidate_summary(
        (winforms_custom, mfc_other, no_pattern),
        WindowHubUIAutomationProvider(),
    )

    by_type = result["by_control_type"]
    assert by_type["custom"]["count"] == 2
    assert by_type["custom"]["visible_count"] == 2
    assert by_type["custom"]["name_present_count"] == 2
    assert by_type["custom"]["automation_id_present_count"] == 1
    assert by_type["custom"]["positive_bounds_count"] == 1
    assert by_type["custom"]["native_handle_present_count"] == 1
    assert by_type["custom"]["value_pattern_count"] == 1
    assert by_type["custom"]["text_pattern_count"] == 1
    assert by_type["other"]["count"] == 1
    assert by_type["other"]["value_pattern_count"] == 1
    assert by_type["other"]["legacy_iaccessible_pattern_count"] == 1

    class_buckets = result["class_bucket_counts"]
    assert class_buckets["custom"]["windows_forms"] == 1
    assert class_buckets["custom"]["class_unavailable"] == 1
    assert class_buckets["other"]["afx_mfc"] == 1

    rendered = repr(result)
    for private_text in (
        "SENSITIVE_CUSTOM_NAME",
        "SENSITIVE_OTHER_NAME",
        "SENSITIVE_EMPTY_NAME",
        "SECRET_AUTOMATION_ID",
        "SECRET_OTHER_ID",
        "WindowsForms10",
        "Afx:Wnd42",
        "501",
        "502",
    ):
        assert private_text not in rendered
