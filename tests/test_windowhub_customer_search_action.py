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


def test_focused_edit_resolves_multiple_inside_picker_candidates():
    first = edit(inside_picker=True, name="Search")
    first["focused"] = False
    second = edit(inside_picker=True)
    second["focused"] = True
    result = classify_customer_search_controls(
        [first, second], picker_focused=False,
    )
    assert result.status == "type_in_unique_search_edit"
    assert result.selected_index == 1
    assert result.reason == "focused_search_edit_inside_lookup"


def test_focus_outside_picker_does_not_resolve_ambiguous_fields():
    inside_a = edit(inside_picker=True)
    inside_a["focused"] = False
    inside_b = edit(inside_picker=True)
    inside_b["focused"] = False
    unrelated = edit(name="Rabat")
    unrelated["focused"] = True
    result = classify_customer_search_controls(
        [inside_a, inside_b, unrelated], picker_focused=True,
    )
    assert result.status == "blocked"
    assert result.reason == "multiple_possible_search_edits"


def test_unique_inside_edit_takes_priority_over_named_field_elsewhere():
    outer = edit(name="Search")
    inner = edit(inside_picker=True, name="")
    result = classify_customer_search_controls(
        [outer, inner], picker_focused=False
    )
    assert result.status == "type_in_unique_search_edit"
    assert result.selected_index == 1


def test_true_child_of_picker_outweighs_overlapping_edit():
    overlap = edit(inside_picker=True)
    overlap["structural_child"] = False
    descendant = edit(inside_picker=True)
    descendant["structural_child"] = True
    result = classify_customer_search_controls(
        [overlap, descendant], picker_focused=False,
    )
    assert result.status == "type_in_unique_search_edit"
    assert result.reason == "unique_customer_picker_child"
    assert result.selected_index == 1


def test_two_true_children_still_block_without_unique_focus():
    left = edit(inside_picker=True)
    left["structural_child"] = True
    right = edit(inside_picker=True)
    right["structural_child"] = True
    result = classify_customer_search_controls(
        [left, right], picker_focused=False,
    )
    assert result.status == "blocked"
    assert result.reason == "multiple_possible_search_edits"


def test_direct_lookup_click_hits_left_text_not_dropdown_arrow():
    from app.agent.offers.windowhub_customer_search_action import direct_lookup_typing_point

    class Rect:
        def width(self):
            return 213
        def height(self):
            return 22

    x, y = direct_lookup_typing_point(Rect())
    assert (x, y) == (34, 11)
    assert x < 213 - 30


def test_direct_lookup_rejects_tiny_or_collapsed_controls():
    import pytest
    from app.agent.offers.windowhub_customer_search_action import direct_lookup_typing_point

    class Rect:
        def width(self):
            return 0
        def height(self):
            return 22

    with pytest.raises(ValueError, match="lookup_geometry_invalid"):
        direct_lookup_typing_point(Rect())
