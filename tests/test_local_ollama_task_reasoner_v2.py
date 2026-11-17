"""Offline regression tests: local Ollama adapter never needs a running model."""
import json
from urllib.error import URLError

from app.agent.reasoning.local_ollama_task_reasoner_v2 import (
    LocalOllamaTaskReasonerV2,
    LOCAL_URL,
)
from app.agent.runtime.computer_use_v2_action_session import ComputerUseV2ActionSession
from tools.smoke_navimind_v2_offline import synthetic_scene


def prepared_request():
    scene = synthetic_scene("Okna - Start1")
    cycle = ComputerUseV2ActionSession().prepare_cycle(
        scene, task_id="local-ollama-test", goal="Test action",
        world_revision=1, observed_at="2026-11-17T06:00:00Z",
    )
    return cycle.request_payload


class FakeResponse:
    def __init__(self, data):
        self.data = data
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return None
    def read(self, size):
        return self.data[:size]


def test_local_provider_emits_protocol_valid_single_action_without_credentials():
    request = prepared_request()
    cap = next(c for c in request["capabilities"]["actions"] if c["name"].startswith("click_ent_"))
    decision = {
        "version": "2", "task_id": request["task_id"], "decision": "act",
        "rationale": "One exposed action", "confidence": 0.9,
        "observation_request": None, "completion": None,
        "requires_manual_review": False,
        "action": {
            "name": cap["name"], "target_ref": cap["target_ref"],
            "value": None, "expected_postcondition": {"kind": "scene_changed"},
            "requires_confirmation": cap["requires_confirmation"],
        },
    }
    def opener(req, timeout):
        assert req.full_url == LOCAL_URL
        assert timeout <= 120
        assert "X-navimind-agent-secret" not in req.headers
        posted = json.loads(req.data)
        assert posted["stream"] is False
        assert posted["model"] == "test-model"
        assert posted["messages"][1]["content"].startswith("{")
        return FakeResponse(json.dumps({"message": {"content": json.dumps(decision)}}).encode())
    engine = LocalOllamaTaskReasonerV2(model="test-model", opener=opener)
    assert engine.reason(request) == decision
    assert engine.last_error is None


def test_provider_connection_failure_is_safe():
    def opener(*args, **kwargs):
        raise URLError("offline")
    engine = LocalOllamaTaskReasonerV2(model="test-model", opener=opener)
    assert engine.reason(prepared_request()) is None
    assert engine.last_error == "local_ai_unavailable_install_or_start_ollama"


def test_provider_invalid_decision_fails_closed():
    def opener(*args, **kwargs):
        return FakeResponse(b'{"message":{"content":"{\"decision\":\"act\"}"}}')
    engine = LocalOllamaTaskReasonerV2(model="test-model", opener=opener)
    assert engine.reason(prepared_request()) is None
    assert engine.last_error == "local_ai_invalid_v2_decision"


def test_cli_parse_accepts_explicit_local_reasoner():
    from tools.run_windowhub_goal_v2 import parse_args
    args = parse_args(["--goal", "Dodaj", "--reasoner", "local-ollama", "--mode", "think"])
    assert args.reasoner == "local-ollama"
    assert args.mode == "think"
