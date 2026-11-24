"""Tests: quote revision routing uses verified effort and preserves original."""
import pytest

from app.agent.offers.navimind_quote_revision_planner import (
    QuoteChange, RevisionRoute, plan_quote_revision,
)


def change(position="1", field="colour", edit=2, rebuild=3, can_edit=True, observed=True):
    return QuoteChange(position, field, "white", "anthracite",
                       edit_steps=edit, rebuild_steps=rebuild,
                       can_edit_existing=can_edit, independently_observed=observed)


def plan(changes=None, **overrides):
    args = dict(
        document_key="OFR/101", changes=changes or (change(),),
        exact_document_verified=True, readback_fresh=True,
        rebuild_possible=True, rebuild_base_steps=5,
    )
    args.update(overrides)
    return plan_quote_revision(**args)


def test_small_change_prefers_edit_existing():
    result = plan()
    assert result.route == RevisionRoute.EDIT_EXISTING
    assert result.edit_cost == 2 and result.rebuild_cost == 8


def test_large_rework_prefers_new_unsaved_draft_not_original_deletion():
    result = plan((change("1", "dimensions", edit=14, rebuild=1),))
    assert result.route == RevisionRoute.REBUILD_DRAFT
    assert result.original_document_preserved and result.create_unsaved_draft_only
    assert not result.save_authorized and not result.send_authorized


def test_equal_effort_prefers_existing_by_default():
    result = plan((change(edit=8, rebuild=3),))
    assert result.route == RevisionRoute.EDIT_EXISTING
    assert result.edit_cost == result.rebuild_cost == 8


def test_equal_effort_can_prefer_rebuild_if_user_chooses():
    result = plan((change(edit=8, rebuild=3),), preserve_existing_preferred=False)
    assert result.route == RevisionRoute.REBUILD_DRAFT


def test_unsupported_edit_can_fall_back_to_new_draft():
    result = plan((change(can_edit=False),))
    assert result.route == RevisionRoute.REBUILD_DRAFT


def test_both_routes_unsupported_request_review():
    result = plan((change(can_edit=False),), rebuild_possible=False)
    assert result.route == RevisionRoute.REVIEW


def test_unknown_original_value_requires_review_not_guessing():
    assert plan((change(observed=False),)).route == RevisionRoute.REVIEW


def test_stale_or_other_document_requires_review():
    assert plan(readback_fresh=False).route == RevisionRoute.REVIEW
    assert plan(exact_document_verified=False).route == RevisionRoute.REVIEW


def test_unknown_dependencies_are_not_silently_ignored():
    unusual = QuoteChange("1", "profile", "a", "b", 3, 2, True, True, ("unknown",))
    assert plan((unusual,)).route == RevisionRoute.REVIEW


def test_multiple_changes_sum_verified_cost_not_count_only():
    result = plan((change("1", "colour", edit=2, rebuild=2),
                   change("2", "price", edit=12, rebuild=1)))
    assert result.edit_cost == 14
    assert result.rebuild_cost == 8
    assert result.route == RevisionRoute.REBUILD_DRAFT


def test_duplicate_position_field_is_rejected():
    with pytest.raises(ValueError, match="duplicate_field_changes"):
        plan((change(), change()))


def test_unbounded_or_unverified_cost_is_rejected():
    with pytest.raises(ValueError, match="invalid_edit_steps"):
        change(edit=-1)
    with pytest.raises(ValueError, match="invalid_rebuild_cost"):
        plan(rebuild_base_steps=-1)
