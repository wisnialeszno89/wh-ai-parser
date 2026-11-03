import pytest

from app.agent.perception.interaction_capability import InteractionCapability
from app.agent.perception.screen_element import ScreenElement
from tools.smoke_windowhub_new_offer_form import summarize_controls


def test_form_inspector_reports_semantics_but_never_field_values():
    element = ScreenElement(
        kind="edit",
        label="Kunde",
        metadata={
            "automation_id": "IDC_CUSTOMER",
            "uia_runtime_id": "7-10-20",
            "uia_enabled": True,
            "uia_focused": True,
            "current_value": "Customer Secret Name",
            "semantic_label_source": "uia_name",
        },
        interaction_capability=InteractionCapability.CLICKABLE,
    )

    records = summarize_controls((element,))

    assert records == (
        {
            "label": "Kunde",
            "control_type": "edit",
            "automation_id": "IDC_CUSTOMER",
            "class_name": "",
            "enabled": True,
            "focused": True,
            "value_present": True,
            "label_source": "uia_name",
        },
    )
    assert "Customer Secret Name" not in str(records)


def test_form_inspector_excludes_unlabeled_and_non_form_elements():
    elements = (
        ScreenElement(kind="edit", label=None),
        ScreenElement(kind="text", label="Customer Secret Name"),
        ScreenElement(kind="button", label="Speichern"),
    )

    records = summarize_controls(elements)

    assert len(records) == 1
    assert records[0]["label"] == "Speichern"


def test_form_inspector_keeps_repeated_labels_with_distinct_runtime_ids():
    elements = (
        ScreenElement(
            kind="checkbox",
            label="Aktiv",
            metadata={"uia_runtime_id": "1"},
        ),
        ScreenElement(
            kind="checkbox",
            label="Aktiv",
            metadata={"uia_runtime_id": "2"},
        ),
    )

    records = summarize_controls(elements)

    assert len(records) == 2


def test_form_inspector_deduplicates_same_uia_control():
    element = ScreenElement(
        kind="edit",
        label="Breite",
        metadata={
            "automation_id": "IDC_WIDTH",
            "uia_runtime_id": "1",
        },
    )

    records = summarize_controls((element, element))

    assert len(records) == 1


@pytest.mark.parametrize("limit", (0, 501, True))
def test_form_inspector_rejects_invalid_control_limits(limit):
    with pytest.raises(ValueError, match="new_offer_form_control_limit_invalid"):
        summarize_controls((), max_controls=limit)
