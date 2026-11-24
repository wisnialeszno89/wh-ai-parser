"""Codespaces V2/V3 shadow comparisons: never execute desktop actions."""
from app.agent.reasoning.navimind_v2_shadow_audit import (
    assess_v2_shadow, shadow_diagnostics,
)


def action(name="click_ent_1", ref="entity-1", **changes):
    data = dict(name=name, target_ref=ref, requires_confirmation=False,
                description="Select a verified UI element")
    data.update(changes)
    return data


def assessment(actions=None, response=None, **flags):
    data = dict(stage="offer_document",
                actions=actions if actions is not None else [action()],
                response=response if response is not None else {
                    "decision": "act", "action": {
                        "name": "click_ent_1", "target_ref": "entity-1"
                    }
                },
                exact_document_verified=True, observation_fresh=True)
    data.update(flags)
    return assess_v2_shadow(**data)


def test_one_unique_v2_action_is_v3_advisory_eligible():
    result = assessment()
    assert result.proposal_decision == "act"
    assert result.v3_decision == "act"
    assert not result.disagreement
    assert not result.execution_affected


def test_shadow_does_not_leak_customer_labels_or_values():
    result = assessment(actions=[action(description="Customer Top Trans private 1234")])
    data = str(shadow_diagnostics(result))
    assert "Top Trans" not in data and "1234" not in data
    assert data.endswith("False}") or "EXECUTION_AFFECTED': False" in data


def test_shadow_rejects_save_and_send_as_advisory_actions():
    for name in ("save_offer", "send_to_client", "Zapisz", "Bestellung_senden"):
        result = assessment(
            actions=[action(name=name)],
            response={"decision": "act", "action": {
                "name": name, "target_ref": "entity-1"
            }},
        )
        assert result.proposal_decision != "act"
        assert result.disagreement
        assert not result.execution_affected


def test_unknown_document_or_stale_screen_never_advises_action():
    assert assessment(exact_document_verified=False).proposal_decision == "observe"
    assert assessment(observation_fresh=False).proposal_decision == "observe"


def test_duplicate_action_refs_cannot_be_treated_as_unique():
    actions = [action(), action(description="Repeated native control")]
    result = assessment(actions=actions)
    assert result.proposal_decision == "observe"
    assert result.disagreement


def test_model_action_not_in_capabilities_is_never_authorized():
    result = assessment(response={
        "decision": "act",
        "action": {"name": "click_ent_unknown", "target_ref": "entity-missing"},
    })
    assert result.proposal_decision == "observe"
    assert result.proposal_reason == "proposal_not_uniquely_exposed"


def test_done_decision_is_flagged_without_independent_postcondition():
    result = assessment(response={"decision": "done", "action": None})
    assert result.disagreement
    assert result.v3_decision != "complete"


def test_confirmation_requirement_blocks_without_operator_approval():
    result = assessment(actions=[action(requires_confirmation=True)])
    assert result.proposal_decision == "ask"
    assert result.disagreement


def test_multiple_safe_actions_require_goal_grounded_choice_but_model_may_propose_one():
    result = assessment(actions=[action(), action("click_ent_2", "entity-2")])
    assert result.v3_decision == "observe"
    assert result.proposal_decision == "act"
    assert not result.disagreement


def test_unknown_stage_remains_read_only():
    result = assessment(stage="unknown")
    assert result.v3_decision == "stop"
    assert result.proposal_decision == "stop"


def test_malformed_or_empty_action_payload_is_safe():
    result = assessment(actions={"bad": "list"})
    assert result.capability_count == 0
    assert result.proposal_decision == "observe"


def test_diagnostics_are_bounded_and_have_no_action_references():
    result = assessment(
        actions=[action("fill_a", "private-id", description="Private client information")]
    )
    fields = shadow_diagnostics(result)
    assert fields["NAVIMIND_SHADOW_EXECUTION_AFFECTED"] is False
    assert "private-id" not in str(fields)
    assert "Private client information" not in str(fields)


def test_unsaved_draft_description_is_not_misclassified_as_save():
    result = assessment(actions=[
        action(description="Select item for an unsaved quotation"),
        action("save_offer", "save-ref", description="Save quotation",
               requires_confirmation=True),
    ])
    assert result.capability_count == 2
    assert result.eligible_count == 1
    assert result.v3_decision == "act"
    assert result.proposal_decision == "act"
    assert result.disagreement is False


def test_real_save_send_and_order_words_remain_protected():
    for name, description in (
        ("save_offer", "Save quotation"),
        ("sendToCustomer", "Send the order"),
        ("submit_order", "Submit new order"),
        ("Speichern", "Speichern des Angebots"),
        ("Zapisz", "Zapisz dokument"),
        ("bestellung_senden", "Bestellung senden"),
        ("delete_position", "Delete item"),
    ):
        result = assessment(
            actions=[action(name, "unsafe-ref", description=description)],
            response={"decision": "act", "action": {
                "name": name, "target_ref": "unsafe-ref"
            }},
        )
        assert result.proposal_decision != "act", name
        assert result.eligible_count == 0, name


def test_unrelated_fragments_do_not_trigger_persistence_classifier():
    for description in (
        "Keep quotation unsaved until reviewed",
        "Preserve and inspect available quotation fields",
        "Select unordered items for a draft",
    ):
        result = assessment(actions=[action(description=description)])
        assert result.proposal_decision == "act", description
        assert result.eligible_count == 1, description
