import json

from app.agent.bridge.world_state import WorldState
from app.agent.reasoning.navimind_task_reasoner import (
    NaviMindTaskReasoner,
    NaviMindTaskReasonerConfig,
)
from app.agent.reasoning.task_planning_context import TaskPlanningContext


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_navimind_reasoner_translates_semantic_action():
    captured = {}

    def opener(request, timeout):
        captured["body"] = request.data
        captured["timeout"] = timeout
        return _Response(
            {
                "version": "1",
                "task_id": "task-1",
                "status": "continue",
                "rationale": "Advance the visible workflow.",
                "confidence": 0.94,
                "action": {
                    "name": "click_screen_element",
                    "description": "Open the next visible section.",
                    "target": "Następna sekcja",
                },
                "requires_manual_review": False,
            }
        )

    reasoner = NaviMindTaskReasoner(
        config=NaviMindTaskReasonerConfig(
            url="http://localhost:3000/api/agent/task",
            timeout_seconds=12,
        ),
        opener=opener,
    )

    proposal = reasoner.reason(
        TaskPlanningContext(
            request_message="Otwórz następną sekcję",
            intent="computer_use",
            session_id="session-1",
            user_id="user-1",
            world=None,
        )
    )

    assert proposal is not None
    assert proposal.status == "continue"
    assert proposal.actions[0].target == "Następna sekcja"
    assert captured["timeout"] == 12
    body = json.loads(captured["body"].decode("utf-8"))
    assert body["version"] == "1"
    assert body["goal"] == "Otwórz następną sekcję"
    assert body["world"]["visible_elements"] == []
