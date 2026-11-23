from app.agent.offers.windowhub_customer_confirmation_policy import (
    can_continue_draft_after_exact_click,
    requires_manual_customer_selection,
)


def test_unverified_native_value_after_exact_clicked_closed_popup_can_continue_draft():
    assert can_continue_draft_after_exact_click(
        "CUSTOMER_CLICKED_BUT_SELECTION_UNVERIFIED_native_selected_value_not_exposed_popup_closed"
    )


def test_partial_unselected_or_popup_open_does_not_authorize_continuation():
    for result in (
        "CUSTOMER_NO_EXACT_SUGGESTION_DURING_TYPING",
        "CUSTOMER_CLICKED_BUT_SELECTION_UNVERIFIED_native_selected_value_not_exposed",
        "EXACT_CUSTOMER_RESULT_AMBIGUOUS",
        "CUSTOMER_TYPING_WINDOW_CHANGED",
    ):
        assert not can_continue_draft_after_exact_click(result)


def test_manual_handoff_only_when_exact_result_missing():
    assert requires_manual_customer_selection("CUSTOMER_NO_EXACT_SUGGESTION_DURING_TYPING")
    assert requires_manual_customer_selection("CUSTOMER_NO_EXACT_RESULT_FOR_SHORT_PREFIX")
    assert not requires_manual_customer_selection("EXACT_CUSTOMER_RESULT_AMBIGUOUS")
    assert not requires_manual_customer_selection(
        "CUSTOMER_CLICKED_BUT_SELECTION_UNVERIFIED_native_selected_value_not_exposed_popup_closed"
    )
