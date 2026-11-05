"""Offline regression for semantic plan vs individually verified WindowHub parts."""
import pytest
from types import SimpleNamespace

from app.agent.learning.windowhub_construction_reconciliation import (
    two_sash_example,
    reconcile_construction,
    reconcile_aggregate_observation,
)


def test_full_nine_step_plan_requires_individual_verification():
    model = two_sash_example()
    result = reconcile_construction(model)
    assert len(result.remaining_ids) == 9
    assert result.next_step.element_id == "frame"
    assert result.status == "proposal_requires_live_verification"


def test_next_step_must_follow_verified_parent():
    model = two_sash_example()
    result = reconcile_construction(
        model, verified_element_ids=("frame", "cell_left", "cell_right")
    )
    assert result.next_step.element_id == "sash_left"
    assert len(result.remaining_ids) == 6


def test_one_sash_does_not_mark_second_sash_verified():
    model = two_sash_example()
    verified = ("frame", "cell_left", "cell_right", "sash_left")
    result = reconcile_construction(model, verified_element_ids=verified)
    assert "sash_right" in result.remaining_ids
    assert result.next_step.element_id == "sash_right"


def test_aggregate_history_is_not_individual_evidence():
    model = two_sash_example()
    history = SimpleNamespace(
        frame_present=True, sash_present=True, glass_present=True,
        construction_present=True, runtime_history_present=True,
        hardware_ready=True,
    )
    result = reconcile_aggregate_observation(model, history)
    assert result.next_step is None
    assert result.status == "observation_insufficient_for_per_element_reconciliation"
    assert len(result.remaining_ids) == 9


def test_enabled_hardware_alone_cannot_prove_installed_hardware():
    result = reconcile_aggregate_observation(
        two_sash_example(),
        SimpleNamespace(hardware_ready=True),
    )
    assert result.next_step is None
    assert "hardware_command_enabled" in result.reason


def test_unrecognized_and_duplicate_verified_ids_are_rejected():
    with pytest.raises(ValueError, match="verified_elements_not_in_target"):
        reconcile_construction(two_sash_example(), verified_element_ids=("wrong",))
    with pytest.raises(ValueError, match="duplicate_verified"):
        reconcile_construction(two_sash_example(), verified_element_ids=("frame", "frame"))


def test_verified_set_only_completes_when_all_ids_proven():
    model = two_sash_example()
    all_ids = tuple(model.elements)
    result = reconcile_construction(model, verified_element_ids=all_ids)
    assert result.status == "plan_fully_verified"
    assert result.next_step is None
    assert not result.remaining_ids
