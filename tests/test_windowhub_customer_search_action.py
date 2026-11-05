"""Customer lookup must search by name, never guess a first row or type elsewhere."""
from app.agent.offers.windowhub_customer_search_action import classify_customer_search_controls


def edit(*, inside_picker=False, name="", enabled=True):
    return {
        "role": "edit", "inside_picker": inside_picker, "name": name,
        "enabled": enabled, "visible": True,
    }


def test_search_edit_inside_picker_wins_over_generic_document_fields():
    result = classify_customer_search_controls(
        [edit(name="Numer oferty"), edit(inside_picker=True, name="")],
        picker_focused=False,
    )
    assert result.status == "type_in_unique_search_edit"
    assert result.search_control_count == 1


def test_focused_lookup_supports_one_typeahead_when_no_search_edit_exposed():
    result = classify_customer_search_controls(
        [edit(name="Rabat")], picker_focused=True,
    )
    assert result.status == "typeahead_on_focused_lookup"


def test_unfocused_lookup_must_not_send_keyboard_input():
    result = classify_customer_search_controls([], picker_focused=False)
    assert result.status == "blocked"


def test_ambiguous_search_edits_block():
    result = classify_customer_search_controls(
        [edit(inside_picker=True), edit(inside_picker=True)],
        picker_focused=True,
    )
    assert result.status == "blocked"
    assert result.reason == "multiple_possible_search_edits"


def test_disabled_search_edit_is_not_used():
    result = classify_customer_search_controls(
        [edit(inside_picker=True, enabled=False)], picker_focused=False,
    )
    assert result.status == "blocked"
