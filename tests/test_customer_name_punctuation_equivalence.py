"""Pure regression checks for punctuation-tolerant customer lookup.

Only full canonical equality may authorize automatic matching.
"""
from app.agent.offers.windowhub_customer_result_selection import (
    Candidate, canonical_customer_name, exact_customer_candidates,
)
from app.agent.offers.windowhub_customer_visual_selection import (
    VisualCustomerResult, match_visual_customer,
)
from app.agent.offers.windowhub_customer_commit_verification import (
    decide_customer_commit,
)


def test_hyphen_equivalent_full_customer_name():
    assert canonical_customer_name("Top Trans Janik Artur") == canonical_customer_name("Top-Trans Janik Artur")
    assert canonical_customer_name("TOP–TRANS  Janik Artur") == canonical_customer_name("Top Trans Janik Artur")


def test_partial_brand_does_not_authorize_selection():
    assert canonical_customer_name("Top-Trans") != canonical_customer_name("Top Trans Janik Artur")
    assert canonical_customer_name("Top-Trans Janik") != canonical_customer_name("Top Trans Janik Artur")


def test_native_visible_full_name_only():
    picker = (100, 100, 350, 130)
    items = [
        Candidate("listitem", "Top-Trans Janik Artur", (120, 150, 300, 170)),
        Candidate("listitem", "Top-Trans", (120, 175, 300, 195)),
    ]
    assert exact_customer_candidates(items, "Top Trans Janik Artur", picker) == [0]


def test_visual_full_name_and_confidence():
    region = (0, 100, 500, 400)
    results = [
        VisualCustomerResult("Top-Trans Janik Artur", .95, (100, 150, 320, 180)),
        VisualCustomerResult("Top-Trans", .96, (100, 190, 200, 220)),
    ]
    assert match_visual_customer(results, "Top Trans Janik Artur", region) == [results[0]]


def test_commit_requires_click_readback_and_closed_popup():
    name = "Top Trans Janik Artur"
    assert decide_customer_commit(
        exact_row_was_clicked=True,
        native_values=("Top-Trans Janik Artur",),
        customer_name=name,
        popup_still_contains_exact_result=False,
    ).status == "verified"
    assert decide_customer_commit(
        exact_row_was_clicked=True,
        native_values=("Top-Trans",),
        customer_name=name,
        popup_still_contains_exact_result=False,
    ).status == "unverified"
    assert decide_customer_commit(
        exact_row_was_clicked=False,
        native_values=("Top-Trans Janik Artur",),
        customer_name=name,
        popup_still_contains_exact_result=False,
    ).status == "unverified"
