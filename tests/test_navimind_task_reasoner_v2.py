import json
from urllib.error import HTTPError, URLError

from app.agent.bridge.agent_task_contract_v2 import AgentTaskV2Contract
from app.agent.reasoning.navimind_task_reasoner import (
    NaviMindTaskReasonerConfig,
)
from app.agent.reasoning.navimind_task_reasoner_v2 import (
    MAX_RESPONSE_BYTES,
    NaviMindTaskReasonerV2,
)


class _Response:
    def __init__(self, payload):
        if isinstance(payload, (bytes, bytearray)):
            self._raw = bytes(payload)
        else:
            self._raw = json.dumps(payload).encode("utf-8")
        self.read_limit = None

    def read(self, size=-1):
        self.read_limit = size
        return self._raw if size < 0 else self._raw[:size]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _request_payload():
    evidence = {
        "ref": "ev_0001",
        "source": "uia",
        "observed_at": "2026-11-02T09:00:00Z",
        "world_revision": 7,
        "scope": "Table structure",
        "confidence": 0.99,
        "content": {
            "kind": "grid_structure",
            "row_count": 8,
            "column_count": 4,
        },
        "limitations": [],
    }
    return {
        "version": "2",
        "task_id": "synthetic-v2-task",
        "goal": "Inspect the visible lookup table structure",
        "intent": "computer_use",
        "session_id": "synthetic-session",
        "task_state": {
            "cycle": 0,
            "max_cycles": 30,
            "reasoning_calls_remaining": 5,
        },
        "world": {
            "revision": 7,
            "observed_at": "2026-11-02T09:00:00Z",
            "application": "WindowHub",
            "window_title": "Nowa oferta",
            "entities": [{
                "ref": "ent_0001",
                "type": "table",
                "label": "Tabela",
                "state": {"visible": True, "enabled": True},
                "attributes": [],
                "confidence": 0.99,
                "evidence_refs": ["ev_0001"],
            }],
            "relationships": [],
            "affordances": [],
            "evidence": [evidence],
        },
        "capabilities": {
            "observations": [{
                "id": "cap_grid_structure",
                "description": "Inspect bounded table structure",
                "target_ref": "ent_0001",
                "input_contract": "table_page_v1",
                "max_items": 10,
                "data_classification": "ui_structure",
                "read_only": True,
            }],
            "actions": [],
        },
        "knowledge": None,
        "experience": [],
        "constraints": {
            "max_observations_per_cycle": 1,
            "max_observation_items": 10,
            "max_evidence_bytes": 2_048,
            "semantic_only": True,
            "verify_each_action": True,
        },
        "metadata": {},
    }


def _observe_response(request_payload):
    return {
        "version": "2",
        "task_id": request_payload["task_id"],
        "decision": "observe",
        "rationale": "The table structure is the next missing evidence.",
        "confidence": 0.9,
        "observation_request": {
            "capability_id": "cap_grid_structure",
            "target_ref": "ent_0001",
            "parameters": {"offset": 0, "limit": 10},
            "based_on_world_revision": 7,
        },
        "action": None,
        "completion": None,
        "requires_manual_review": False,
    }


def _reasoner(opener, *, secret="test-secret", timeout=12):
    return NaviMindTaskReasonerV2(
        config=NaviMindTaskReasonerConfig(
            url="http://localhost:3000/api/agent/task",
            secret=secret,
            timeout_seconds=timeout,
        ),
        opener=opener,
    )


def test_v2_reasoner_posts_contract_and_returns_validated_observe_decision():
    captured = {}

    def opener(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        captured["headers"] = {
            key.lower(): value for key, value in request.header_items()
        }
        response = _observe_response(captured["body"])
        return _Response(response)

    reasoner = _reasoner(opener)
    request_payload = _request_payload()
    response = reasoner.reason(request_payload)

    assert response is not None
    assert response["decision"] == "observe"
    assert response["version"] == "2"
    assert response["task_id"] == request_payload["task_id"]
    assert captured["body"] == request_payload
    assert captured["timeout"] == 12
    assert captured["headers"]["content-type"] == "application/json"
    assert captured["headers"]["accept"] == "application/json"
    assert captured["headers"]["x-navimind-agent-secret"] == "test-secret"
    assert reasoner.last_error is None


def test_v2_reasoner_can_send_a_contract_object_without_translating_it_to_v1():
    captured = {}

    def opener(request, timeout):
        payload = json.loads(request.data.decode("utf-8"))
        captured["version"] = payload["version"]
        return _Response(_observe_response(payload))

    reasoner = _reasoner(opener)
    request_contract = AgentTaskV2Contract.from_payload(_request_payload())
    response = reasoner.reason(request_contract)

    assert response is not None
    assert captured["version"] == "2"
    assert "status" not in response
    assert response["decision"] == "observe"


def test_v2_reasoner_rejects_invalid_request_before_network_call():
    calls = []

    def opener(request, timeout):
        calls.append(request)
        return _Response({})

    reasoner = _reasoner(opener)
    request_payload = _request_payload()
    request_payload["capabilities"]["observations"][0]["target_ref"] = "not_in_world"

    assert reasoner.reason(request_payload) is None
    assert reasoner.last_error.startswith("invalid_v2_request:")
    assert calls == []


def test_v2_reasoner_rejects_stale_or_unexposed_model_observation():
    def opener(request, timeout):
        payload = json.loads(request.data.decode("utf-8"))
        response = _observe_response(payload)
        response["observation_request"]["based_on_world_revision"] = 6
        return _Response(response)

    reasoner = _reasoner(opener)
    assert reasoner.reason(_request_payload()) is None
    assert reasoner.last_error.startswith("invalid_navimind_v2_decision:")


def test_v2_reasoner_returns_validated_manual_review_decision():
    def opener(request, timeout):
        payload = json.loads(request.data.decode("utf-8"))
        return _Response({
            "version": "2",
            "task_id": payload["task_id"],
            "decision": "manual_review",
            "rationale": "No approved capability is available.",
            "confidence": 0,
            "observation_request": None,
            "action": None,
            "completion": None,
            "requires_manual_review": True,
        })

    reasoner = _reasoner(opener)
    response = reasoner.reason(_request_payload())

    assert response is not None
    assert response["decision"] == "manual_review"
    assert response["requires_manual_review"] is True


def test_v2_reasoner_rejects_wrong_task_id_and_extra_response_fields():
    def opener(request, timeout):
        payload = json.loads(request.data.decode("utf-8"))
        response = _observe_response(payload)
        response["task_id"] = "different-task"
        return _Response(response)

    reasoner = _reasoner(opener)
    assert reasoner.reason(_request_payload()) is None
    assert "response_task_id_mismatch" in reasoner.last_error


def test_v2_reasoner_rejects_invalid_json_and_non_object_response():
    for raw in (b"{", b"[]"):
        reasoner = _reasoner(lambda request, timeout: _Response(raw))
        assert reasoner.reason(_request_payload()) is None
        assert reasoner.last_error in {
            "invalid_navimind_v2_json",
            "invalid_navimind_v2_response",
        }


def test_v2_reasoner_bounds_response_body_read():
    response = _Response(b"x" * (MAX_RESPONSE_BYTES + 1))
    reasoner = _reasoner(lambda request, timeout: response)

    assert reasoner.reason(_request_payload()) is None
    assert reasoner.last_error == "navimind_v2_response_too_large"
    assert response.read_limit == MAX_RESPONSE_BYTES + 1


def test_v2_reasoner_reports_http_and_network_failures_without_response_body():
    def http_error(request, timeout):
        raise HTTPError(
            request.full_url,
            401,
            "Unauthorized",
            hdrs=None,
            fp=None,
        )

    reasoner = _reasoner(http_error)
    assert reasoner.reason(_request_payload()) is None
    assert reasoner.last_error == "navimind_http_401"

    def network_error(request, timeout):
        raise URLError("offline")

    reasoner = _reasoner(network_error)
    assert reasoner.reason(_request_payload()) is None
    assert reasoner.last_error.startswith("navimind_connection_error:")


def test_v2_reasoner_omits_secret_header_when_not_configured():
    captured = {}

    def opener(request, timeout):
        captured["headers"] = {
            key.lower(): value for key, value in request.header_items()
        }
        payload = json.loads(request.data.decode("utf-8"))
        return _Response(_observe_response(payload))

    reasoner = _reasoner(opener, secret=None)
    assert reasoner.reason(_request_payload()) is not None
    assert "x-navimind-agent-secret" not in captured["headers"]
