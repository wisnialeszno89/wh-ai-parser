"""Exact customer matching tests: existing records only, never guess."""
from app.agent.offers.windowhub_customer_result_selection import (
    Candidate, nearby_lookup, exact_customer_candidates,
)

PICKER = (284, 287, 497, 309)


def item(role, name, rect=(290, 320, 470, 344), **kwargs):
    return Candidate(role, name, rect, **kwargs)


def test_exact_customer_visible_text_row_is_accepted():
    rows = [item("Text", "Top Trans"), item("Text", "Top Transport")]
    assert exact_customer_candidates(rows, "Top Trans", PICKER) == [0]


def test_typing_inside_lookup_is_not_evidence_of_selected_record():
    rows = [item("Text", "Top Trans", rect=(284, 287, 497, 309))]
    assert exact_customer_candidates(rows, "Top Trans", PICKER) == []


def test_nearby_popup_custom_row_is_accepted():
    rows = [item("Custom", "Top Trans", rect=(295, 351, 495, 379))]
    assert exact_customer_candidates(rows, "Top Trans", PICKER) == [0]


def test_other_offer_window_result_does_not_match():
    rows = [item("Text", "Top Trans", rect=(800, 800, 1000, 830))]
    assert exact_customer_candidates(rows, "Top Trans", PICKER) == []


def test_ambiguous_duplicate_exact_matches_are_not_unique():
    rows = [item("Text", "Top Trans"), item("Custom", "Top Trans")]
    assert len(exact_customer_candidates(rows, "Top Trans", PICKER)) == 2


def test_disabled_or_hidden_match_rejected():
    rows = [item("Text", "Top Trans", enabled=False),
            item("Custom", "Top Trans", visible=False)]
    assert exact_customer_candidates(rows, "Top Trans", PICKER) == []


def test_bounded_dropdown_region_nearby():
    assert nearby_lookup((300, 320, 500, 340), PICKER)
    assert not nearby_lookup((30, 1200, 330, 1250), PICKER)


def test_customer_suggestion_matches_whole_prefix_words():
    from app.agent.offers.windowhub_customer_result_selection import customer_name_completes_query

    assert customer_name_completes_query("Top Trans Artur Janik", "top trans")
    assert not customer_name_completes_query("Top Transport Artur Janik", "Top Trans")
    assert not customer_name_completes_query("Top Trans", "Top Trans")
    assert not customer_name_completes_query("Firma Top Trans Artur Janik", "Top Trans")


def test_reordered_registered_name_is_a_suggestion_without_exact_click_authority():
    from app.agent.offers.windowhub_customer_result_selection import customer_name_has_reordered_words

    requested = "Top Trans Artur Janik"
    registered = "Top Trans Janik Artur"
    assert customer_name_has_reordered_words(registered, requested)
    assert not customer_name_has_reordered_words("Top Trans Janik Adam", requested)
    assert not customer_name_has_reordered_words("Trans Top Janik Artur", requested)
    assert exact_customer_candidates(
        [Candidate("dataitem", registered, (310, 335, 440, 359))], requested, PICKER,
    ) == []
