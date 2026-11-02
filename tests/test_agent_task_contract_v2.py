import copy

import pytest

from app.agent.bridge.agent_task_contract_v2 import (
    AgentTaskV2Contract,
    validate_agent_task_v2_payload,
    validate_agent_task_v2_response,
)


def make_request():
    return {
        "version": "2",
        "task_id": "task-001",
        "goal": "Find the requested customer record.",
        "intent": "computer_use",
        "session_id": "session-001",
        "task_state": {
            "cycle": 3,
            "max_cycles": 30,
            "reasoning_calls_remaining": 5,
        },
        "world": {
            "revision": 12,
            "observed_at": "2026-11-02T06:00:00Z",
            "application": "WindowHub",
            "window_title": "Zamawiający",
            "entities": [
                {
                    "ref": "ent_customer_lookup",
                    "type": "lookup_field",
                    "label": "Zamawiający",
                    "state": {"enabled": True, "visible": True, "value_present": False},
                    "attributes": [],
                    "confidence": 0.99,
                    "evidence_refs": ["ev_lookup"],
                },
                {
                    "ref": "ent_customer_grid",
                    "type": "table",
                    "label": "Lista klientów",
                    "state": {"enabled": True, "visible": True},
                    "attributes": [],
                    "confidence": 0.99,
                    "evidence_refs": ["ev_grid"],
                },
            ],
            "relationships": [
                {
                    "from_ref": "ent_customer_grid",
                    "relationship": "belongs_to",
                    "to_ref": "ent_customer_lookup",
                    "confidence": 0.98,
                    "evidence_refs": ["ev_grid"],
                }
            ],
            "affordances": [],
            "evidence": [
                {
                    "ref": "ev_lookup",
                    "source": "uia",
                    "observed_at": "2026-11-02T06:00:00Z",
                    "world_revision": 12,
                    "scope": "customer lookup field",
                    "confidence": 0.99,
                    "content": {"role": "lookup_field"},
                    "limitations": [],
                },
                {
                    "ref": "ev_grid",
                    "source": "uia",
                    "observed_at": "2026-11-02T06:00:00Z",
                    "world_revision": 12,
                    "scope": "customer lookup table",
                    "confidence": 0.99,
                    "content": {"reported_columns": 4},
                    "limitations": ["Reported row count is not confirmed record count."],
                },
            ],
        },
        "capabilities": {
            "observations": [
                {
                    "id": "read_table_page",
                    "description": "Read a bounded page of rows from the semantic table.",
                    "target_ref": "ent_customer_grid",
                    "input_contract": "table_page_v1",
                    "max_items": 20,
                    "data_classification": "business_records",
                    "read_only": True,
                }
            ],
            "actions": [
                {
                    "name": "open_lookup",
                    "description": "Open the customer lookup list.",
                    "target_ref": "ent_customer_lookup",
                    "requires_confirmation": False,
                }
            ],
        },
        "knowledge": None,
        "experience": [],
        "constraints": {
            "max_observations_per_cycle": 1,
            "max_observation_items": 20,
            "max_evidence_bytes": 32_768,
            "semantic_only": True,
            "verify_each_action": True,
        },
        "metadata": {},
    }


def make_response(decision="observe"):
    return {
        "version": "2",
        "task_id": "task-001",
        "decision": decision,
        "rationale": "The matching customer has not been identified yet.",
        "confidence": 0.96,
        "observation_request": {
            "capability_id": "read_table_page",
            "target_ref": "ent_customer_grid",
            "parameters": {"offset": 0, "limit": 10, "text_query": "Example GmbH"},
            "based_on_world_revision": 12,
        },
        "action": None,
        "completion": None,
        "requires_manual_review": False,
    }


def test_v2_contract_round_trips_a_bounded_request():
    payload = make_request()

    validate_agent_task_v2_payload(payload)
    contract = AgentTaskV2Contract.from_payload(payload)

    assert contract.to_payload() == payload


def test_v2_contract_rejects_v1_version_and_unknown_top_level_fields():
    payload = make_request()
    payload["version"] = "1"

    with pytest.raises(ValueError, match="unsupported_version"):
        validate_agent_task_v2_payload(payload)

    payload = make_request()
    payload["debug_dump"] = {"anything": True}

    with pytest.raises(ValueError, match="unknown_fields"):
        validate_agent_task_v2_payload(payload)


def test_v2_contract_rejects_provider_native_fields_recursively():
    payload = make_request()
    payload["world"]["entities"][0]["state"]["automation_id"] = "IDC_CUSTOMER"

    with pytest.raises(ValueError, match="provider_field"):
        validate_agent_task_v2_payload(payload)


def test_v2_contract_rejects_duplicate_or_unresolved_semantic_refs():
    payload = make_request()
    payload["world"]["entities"][1]["ref"] = "ent_customer_lookup"

    with pytest.raises(ValueError, match="entity_refs_duplicate"):
        validate_agent_task_v2_payload(payload)

    payload = make_request()
    payload["world"]["relationships"][0]["to_ref"] = "ent_missing"

    with pytest.raises(ValueError, match="unknown_entity"):
        validate_agent_task_v2_payload(payload)


def test_v2_contract_rejects_unknown_evidence_refs():
    payload = make_request()
    payload["world"]["entities"][0]["evidence_refs"] = ["ev_missing"]

    with pytest.raises(ValueError, match="unknown_evidence"):
        validate_agent_task_v2_payload(payload)


def test_v2_contract_rejects_non_read_only_observation_capability():
    payload = make_request()
    payload["capabilities"]["observations"][0]["read_only"] = False

    with pytest.raises(ValueError, match="read_only"):
        validate_agent_task_v2_payload(payload)


def test_v2_observe_decision_accepts_only_exposed_bounded_table_page():
    request = make_request()
    response = make_response()

    validate_agent_task_v2_response(response, request)


def test_v2_observe_decision_rejects_unknown_capability_and_stale_revision():
    request = make_request()
    response = make_response()
    response["observation_request"]["capability_id"] = "dump_database"

    with pytest.raises(ValueError, match="capability_not_exposed"):
        validate_agent_task_v2_response(response, request)

    response = make_response()
    response["observation_request"]["based_on_world_revision"] = 11

    with pytest.raises(ValueError, match="out_of_bounds"):
        validate_agent_task_v2_response(response, request)


def test_v2_observe_decision_enforces_capability_page_limit():
    request = make_request()
    response = make_response()
    response["observation_request"]["parameters"]["limit"] = 21

    with pytest.raises(ValueError, match="out_of_bounds"):
        validate_agent_task_v2_response(response, request)


def test_v2_act_decision_requires_exposed_action_and_typed_postcondition():
    request = make_request()
    response = make_response("act")
    response["observation_request"] = None
    response["action"] = {
        "name": "open_lookup",
        "target_ref": "ent_customer_lookup",
        "value": None,
        "expected_postcondition": {
            "kind": "entity_state_equals",
            "target_ref": "ent_customer_lookup",
            "state": "expanded",
            "expected_value": True,
        },
        "requires_confirmation": False,
    }

    validate_agent_task_v2_response(response, request)

    response["action"]["name"] = "execute_shell_command"
    with pytest.raises(ValueError, match="action_not_exposed"):
        validate_agent_task_v2_response(response, request)


def test_v2_act_decision_cannot_downgrade_confirmation_or_use_unknown_target():
    request = make_request()
    response = make_response("act")
    response["observation_request"] = None
    response["action"] = {
        "name": "open_lookup",
        "target_ref": "ent_missing",
        "value": None,
        "expected_postcondition": {
            "kind": "entity_state_equals",
            "target_ref": "ent_customer_lookup",
            "state": "expanded",
            "expected_value": True,
        },
        "requires_confirmation": False,
    }

    with pytest.raises(ValueError, match="unknown_entity"):
        validate_agent_task_v2_response(response, request)

    request["capabilities"]["actions"][0]["requires_confirmation"] = True
    response["action"]["target_ref"] = "ent_customer_lookup"
    with pytest.raises(ValueError, match="confirmation_cannot_be_downgraded"):
        validate_agent_task_v2_response(response, request)


def test_v2_done_requires_evidence_from_the_current_world():
    request = make_request()
    response = make_response("done")
    response["observation_request"] = None
    response["completion"] = {"evidence_refs": ["ev_grid"]}

    validate_agent_task_v2_response(response, request)

    response["completion"] = {"evidence_refs": []}
    with pytest.raises(ValueError, match="requires_evidence"):
        validate_agent_task_v2_response(response, request)

    response["completion"] = {"evidence_refs": ["ev_missing"]}
    with pytest.raises(ValueError, match="unknown_evidence"):
        validate_agent_task_v2_response(response, request)


def test_v2_manual_review_is_a_stop_with_no_other_payload():
    request = make_request()
    response = make_response("manual_review")
    response["observation_request"] = None
    response["requires_manual_review"] = True
    response["rationale"] = "Two customer records match; the user must choose."

    validate_agent_task_v2_response(response, request)

    response["action"] = {"name": "open_lookup"}
    with pytest.raises(ValueError, match="incompatible_payload"):
        validate_agent_task_v2_response(response, request)


def test_v2_response_must_match_request_task_and_version():
    request = make_request()
    response = make_response()
    response["task_id"] = "another-task"

    with pytest.raises(ValueError, match="task_id_mismatch"):
        validate_agent_task_v2_response(response, request)

    response = make_response()
    response["version"] = "1"
    with pytest.raises(ValueError, match="version_mismatch"):
        validate_agent_task_v2_response(response, request)


def test_v2_response_decision_variants_are_mutually_exclusive():
    request = make_request()
    response = make_response()
    response["action"] = {
        "name": "open_lookup",
        "target_ref": "ent_customer_lookup",
        "value": None,
        "expected_postcondition": {
            "kind": "entity_state_equals",
            "target_ref": "ent_customer_lookup",
            "state": "expanded",
            "expected_value": True,
        },
        "requires_confirmation": False,
    }

    with pytest.raises(ValueError, match="incompatible_payload"):
        validate_agent_task_v2_response(response, request)


def test_v2_contract_does_not_mutate_the_callers_payload():
    payload = make_request()
    original = copy.deepcopy(payload)

    validate_agent_task_v2_payload(payload)

    assert payload == original
