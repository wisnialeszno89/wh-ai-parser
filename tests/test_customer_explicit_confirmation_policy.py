from app.agent.offers.windowhub_customer_confirmation_policy import (
    can_request_customer_attestation, valid_customer_attestation,
)


def _approval(**changes):
    params = dict(
        typed_name="Top-Trans Janik Artur",
        expected_name="Top Trans Janik Artur",
        stage="document_properties",
        original_hwnd=77,
        observed_hwnd=77,
        observed_customer_value=None,
    )
    params.update(changes)
    return valid_customer_attestation(**params)


def test_exact_clicked_closed_popup_eligible_only():
    assert can_request_customer_attestation(
        "CUSTOMER_CLICKED_BUT_SELECTION_UNVERIFIED_native_selected_value_not_exposed_popup_closed"
    )
    assert not can_request_customer_attestation("CUSTOMER_NO_EXACT_SUGGESTION_DURING_TYPING")
    assert not can_request_customer_attestation(
        "CUSTOMER_CLICKED_BUT_SELECTION_UNVERIFIED_native_selected_value_not_exposed"
    )


def test_explicit_full_customer_name_accepts_hyphen_equivalence():
    assert _approval()
    assert _approval(observed_customer_value="Top-Trans Janik Artur")


def test_no_generic_approval_or_partial_name():
    assert not _approval(typed_name="tak")
    assert not _approval(typed_name="Top-Trans")
    assert not _approval(typed_name="Top-Trans Janik")


def test_window_and_stage_stability_mandatory():
    assert not _approval(stage="start")
    assert not _approval(observed_hwnd=88)
    assert not _approval(original_hwnd=None)


def test_conflicting_native_customer_readback_wins():
    assert not _approval(observed_customer_value="Top-Trans Jan Kowalski")
