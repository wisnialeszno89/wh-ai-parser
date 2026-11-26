"""No-network contract and decision tests for the synthetic V2 smoke runner."""
from tools.smoke_navimind_v2_reasoning import run_once, synthetic_request
from app.agent.bridge.agent_task_contract_v2 import validate_agent_task_v2_payload


def test_synthetic_request_is_valid_and_has_no_actions():
    payload = synthetic_request()
    validate_agent_task_v2_payload(payload)
    assert payload["capabilities"]["actions"] == []
    assert payload["world"]["application"] == "SyntheticTableDemo"
    assert "Top Trans" not in str(payload)
    assert "WindowHub" not in str(payload)


def test_synthetic_smoke_validates_server_decision_without_actions():
    class FakeReasoner:
        last_error = None

        def reason(self, payload):
            assert payload["capabilities"]["actions"] == []
            return {
                "version": "2",
                "task_id": payload["task_id"],
                "decision": "manual_review",
                "rationale": "Synthetic read-only test needs no desktop action.",
                "confidence": 0.5,
                "observation_request": None,
                "action": None,
                "completion": None,
                "requires_manual_review": True,
            }

    assert run_once(FakeReasoner()) == (True, "manual_review")


def test_synthetic_smoke_hides_unexpected_error_details():
    class FakeReasoner:
        last_error = "invalid_navimind_v2_decision:secret-looking-untrusted-text"

        def reason(self, payload):
            return None

    assert run_once(FakeReasoner()) == (
        False, "invalid_navimind_v2_decision",
    )
