"""Offline report contract. No WindowHub process or model API required."""
from copy import deepcopy

import pytest

from app.agent.bridge.windowhub_sales_mission_review import (
    ReviewEvidence,
    build_review_report,
    compact_review_summary,
)


def _mission():
    return {
        "mission_id": "test-four-windows",
        "customer": {"exact_name": "Top Trans Janik Artur"},
        "global": {
            "system": "Perfectline",
            "color_external": "antracyt",
            "color_internal": "biały",
            "glazing_panes": 2,
            "discount_window_percent": 20,
        },
        "positions": [
            {
                "index": 1, "kind": "window", "quantity": 1,
                "width_mm": 1640, "height_mm": 1010, "layout": "two_sashes",
                "opening": "requires_approval", "box_above_marked": True,
                "roller_position": {"box_height_mm": None, "overall_height_mm": None},
            },
            {
                "index": 2, "kind": "window", "quantity": 1,
                "width_mm": 1020, "height_mm": 1010, "layout": "single_sash",
                "opening": "requires_approval", "box_above_marked": False,
            },
        ],
    }


def _live(position, field, value):
    return ReviewEvidence(position, field, value, True, "windowhub_live_readback")


def test_empty_evidence_does_not_invent_completed_windows_or_customer():
    result = build_review_report(_mission(), customer_selection="exact_result_clicked_popup_closed")
    assert result["verified_field_count"] == 0
    assert not result["mission_complete_verified"]
    assert not result["save_authorized"]
    assert not result["send_authorized"]
    assert not result["customer_commit_verified"]
    assert all(not p["fully_matches_request"] for p in result["positions"])
    assert any(i["field"] == "customer" for i in result["unresolved"])
    assert "Save/send authorized: NO" in compact_review_summary(result)


def test_matching_dimension_is_verified_and_conflict_is_explicit():
    report = build_review_report(_mission(), (
        _live(1, "width_mm", 1640),
        _live(1, "height_mm", 1050),
    ), customer_commit_verified=True)
    fields = {f["field"]: f for f in report["positions"][0]["fields"]}
    assert fields["width_mm"]["status"] == "verified_matches_request"
    assert fields["height_mm"]["status"] == "verified_differs_from_request"
    assert fields["height_mm"]["requested"] == 1010
    assert fields["height_mm"]["observed"] == 1050
    assert "customer" not in {entry["field"] for entry in report["unresolved"]}


def test_unknown_box_height_stays_reviewable_even_after_live_readback():
    result = build_review_report(_mission(), (
        _live(1, "roller_box_height_mm", 180),
    ))
    item = next(f for f in result["positions"][0]["fields"] if f["field"] == "roller_box_height_mm")
    assert item["status"] == "catalogue_value_needs_salesperson_review"
    assert item["observed"] == 180


def test_never_accept_unverified_or_model_claims_as_live_evidence():
    for proof in (
        ReviewEvidence(1, "width_mm", 1640, False, "windowhub_live_readback"),
        ReviewEvidence(1, "width_mm", 1640, True, "model_reasoning"),
    ):
        with pytest.raises(ValueError, match="unverified_evidence"):
            build_review_report(_mission(), (proof,))


def test_reject_duplicate_evidence_and_invalid_position():
    with pytest.raises(ValueError, match="conflicting_or_repeated_evidence"):
        build_review_report(_mission(), (
            _live(1, "width_mm", 1640),
            _live(1, "width_mm", 1640),
        ))
    with pytest.raises(ValueError, match="invalid_evidence_position"):
        build_review_report(_mission(), (_live(9, "width_mm", 1000),))


def test_mission_is_not_mutated():
    mission = _mission()
    original = deepcopy(mission)
    build_review_report(mission)
    assert mission == original
