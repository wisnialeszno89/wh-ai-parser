from types import SimpleNamespace

from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.windowhub_ui_automation_provider import (
    WindowHubUIAutomationProvider,
)
from tools.diagnose_windowhub_field_scope import (
    _scene_field_element_census,
    _summarize_uia_field_candidates,
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
    ):
        self.element_info = SimpleNamespace(
            name=name,
            control_type=control_type,
            visible=visible,
            enabled=True,
            handle=handle,
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
