"""Customer click is not completion without independent postcondition."""
from app.agent.offers.windowhub_customer_commit_verification import decide_customer_commit


def test_exact_click_plus_native_readback_plus_closed_popup():
    result = decide_customer_commit(
        exact_row_was_clicked=True, native_values=("Top Trans",),
        customer_name="Top Trans", popup_still_contains_exact_result=False,
    )
    assert result.status == "verified"


def test_typed_customer_name_cannot_be_assumed_selected():
    result = decide_customer_commit(
        exact_row_was_clicked=False, native_values=("Top Trans",),
        customer_name="Top Trans", popup_still_contains_exact_result=False,
    )
    assert result.status == "unverified"


def test_popup_still_open_requires_more_evidence():
    result = decide_customer_commit(
        exact_row_was_clicked=True, native_values=("Top Trans",),
        customer_name="Top Trans", popup_still_contains_exact_result=True,
    )
    assert result.status == "unverified"


def test_missing_native_business_value_stops():
    result = decide_customer_commit(
        exact_row_was_clicked=True, native_values=(),
        customer_name="Top Trans", popup_still_contains_exact_result=False,
    )
    assert result.status == "unverified"


def test_other_customer_value_does_not_satisfy():
    result = decide_customer_commit(
        exact_row_was_clicked=True, native_values=("Top Transport",),
        customer_name="Top Trans", popup_still_contains_exact_result=False,
    )
    assert result.status == "unverified"
