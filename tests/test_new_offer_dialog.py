from dataclasses import asdict
from types import SimpleNamespace

from app.agent.perception.screen_element import ScreenElement
from app.wh.runtime.dialogs.new_offer_dialog import NewOfferDialog


def make_element(
    *,
    label="Rabat",
    automation_id="IDC_RABAT",
    kind="edit",
    source="windowhub_ui_automation",
    owned_modal=True,
    enabled=True,
    visible=True,
    runtime_id="42-7-19",
    ancestors=(),
    current_value="PRIVATE CURRENT VALUE",
):
    return ScreenElement(
        kind=kind,
        label=label,
        x=100,
        y=100,
        width=120,
        height=24,
        confidence=0.99,
        metadata={
            "source": source,
            "automation_id": automation_id,
            "uia_control_type": kind,
            "uia_owned_modal": owned_modal,
            "uia_enabled": enabled,
            "uia_visible": visible,
            "uia_runtime_id": runtime_id,
            "uia_ancestor_context": ancestors,
            "current_value": current_value,
        },
    )


def make_scene(*elements):
    return SimpleNamespace(elements=tuple(elements))


def test_resolves_exact_field_in_owned_new_offer_dialog_without_exposing_value():
    element = make_element()
    result = NewOfferDialog().resolve_field(make_scene(element), "discount")

    assert result.status == "resolved"
    assert result.candidate_count == 1
    assert result.binding is not None
    assert result.binding.key == "discount"
    assert result.binding.automation_id == "IDC_RABAT"
    assert result.binding.operation == "number"
    assert result.binding.target_label == "Rabat"
    assert result.binding.control_type == "edit"
    assert result.binding.runtime_id == "42-7-19"
    assert "PRIVATE CURRENT VALUE" not in str(asdict(result.binding))


def test_lookup_editor_is_classified_as_lookup_not_free_text():
    element = make_element(
        label="Klient",
        automation_id="IDC_ZAMAWIAJACY",
        kind="button",
    )

    result = NewOfferDialog().resolve_field(make_scene(element), "customer")

    assert result.status == "resolved"
    assert result.binding is not None
    assert result.binding.operation == "lookup"
    assert result.binding.control_type == "button"


def test_date_field_matches_child_editor_with_exact_parent_calendar_automation_id():
    date_editor = make_element(
        label="Data realizacji",
        automation_id="dateDisplay",
        kind="edit",
        ancestors=(
            ("custom", "WHCalendar", "LayoutItem", "IDC_RELIZACJA", 900),
            ("pane", "LayoutItem", "LayoutItem", "", 900),
        ),
    )
    repeated_inner_editor = make_element(
        label="Data realizacji",
        automation_id="PART_Editor",
        kind="edit",
        ancestors=(
            ("custom", "WHCalendar", "LayoutItem", "IDC_RELIZACJA", 900),
        ),
    )
    other_date_editor = make_element(
        label="Data odbioru",
        automation_id="dateDisplay",
        kind="edit",
        ancestors=(
            ("custom", "WHCalendar", "LayoutItem", "IDC_ODBIOR", 901),
        ),
    )

    result = NewOfferDialog().resolve_field(
        make_scene(date_editor, repeated_inner_editor, other_date_editor),
        "realization_date",
    )

    assert result.status == "resolved"
    assert result.binding is not None
    assert result.binding.automation_id == "dateDisplay"
    assert result.binding.operation == "date"
    assert result.binding.target_label == "Data realizacji"


def test_unowned_control_cannot_be_resolved_as_new_offer_field():
    element = make_element(owned_modal=False)

    result = NewOfferDialog().resolve_field(make_scene(element), "discount")

    assert result.status == "blocked"
    assert result.binding is None
    assert "owned modal" in result.reason


def test_untrusted_control_cannot_be_resolved():
    element = make_element(source="windowhub_ocr")

    result = NewOfferDialog().resolve_field(make_scene(element), "discount")

    assert result.status == "blocked"
    assert result.binding is None
    assert "provenance" in result.reason


def test_duplicate_field_identity_is_ambiguous_even_when_one_candidate_is_modal():
    modal = make_element(runtime_id="42-7-19")
    non_modal = make_element(owned_modal=False, runtime_id="42-7-20")

    result = NewOfferDialog().resolve_field(
        make_scene(modal, non_modal),
        "discount",
    )

    assert result.status == "ambiguous"
    assert result.candidate_count == 2
    assert result.binding is None


def test_disabled_or_invisible_field_is_blocked():
    disabled = make_element(enabled=False)

    result = NewOfferDialog().resolve_field(make_scene(disabled), "discount")

    assert result.status == "blocked"
    assert "enabled" in result.reason


def test_field_without_runtime_id_is_blocked():
    element = make_element(runtime_id=None)

    result = NewOfferDialog().resolve_field(make_scene(element), "discount")

    assert result.status == "blocked"
    assert "RuntimeId" in result.reason


def test_wrong_control_role_is_blocked():
    element = make_element(kind="button")

    result = NewOfferDialog().resolve_field(make_scene(element), "discount")

    assert result.status == "blocked"
    assert "role mismatch" in result.reason


def test_unknown_field_key_is_not_guessed():
    result = NewOfferDialog().resolve_field(make_scene(), "unknown customer")

    assert result.status == "missing"
    assert result.binding is None
    assert "Unknown" in result.reason


def test_resolve_all_returns_read_only_results_for_the_declared_dialog_map():
    element = make_element()
    results = NewOfferDialog().resolve_all(make_scene(element))

    assert len(results) == len(NewOfferDialog.FIELD_SPECS)
    assert sum(item.status == "resolved" for item in results) == 1
    assert next(item for item in results if item.key == "discount").status == "resolved"
    assert all(item.binding is None or item.binding.target_label for item in results)
