import json

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


def test_navimind_reasoner_sends_explicit_allowed_actions():
    captured = {}

    def opener(request, timeout):
        captured["body"] = request.data
        captured["timeout"] = timeout
        return _Response(
            {
                "version": "1",
                "task_id": "task-1",
                "status": "continue",
                "rationale": "Use the visible control.",
                "confidence": 0.9,
                "action": {
                    "name": "click_screen_element",
                    "description": "Click the visible control.",
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

    # Capture the generated task id so the response satisfies the
    # correlation check introduced by the bridge.
    original_opener = opener

    def correlated_opener(request, timeout):
        body = json.loads(request.data.decode("utf-8"))
        captured["task"] = body
        response = _Response(
            {
                "version": "1",
                "task_id": body["task_id"],
                "status": "continue",
                "rationale": "Use the visible control.",
                "confidence": 0.9,
                "action": {
                    "name": "click_screen_element",
                    "description": "Click the visible control.",
                    "target": "Następna sekcja",
                },
                "requires_manual_review": False,
            }
        )
        captured["timeout"] = timeout
        return response

    reasoner.opener = correlated_opener

    proposal = reasoner.reason(
        TaskPlanningContext(
            request_message="Otwórz następną sekcję",
            intent="computer_use",
        )
    )

    assert proposal is not None
    assert (
        "click_screen_element"
        in captured["task"]["constraints"]["allowed_actions"]
    )
    assert (
        "write_text"
        in captured["task"]["constraints"]["allowed_actions"]
    )
    assert len(
        captured["task"]["constraints"]["allowed_actions"]
    ) > 0


def test_navimind_reasoner_rejects_action_outside_local_policy():
    def opener(request, timeout):
        body = json.loads(request.data.decode("utf-8"))
        return _Response(
            {
                "version": "1",
                "task_id": body["task_id"],
                "status": "continue",
                "rationale": "Unsafe operation.",
                "confidence": 0.9,
                "action": {
                    "name": "execute_shell_command",
                    "description": "Run a local command.",
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
            request_message="Zrób coś",
            intent="computer_use",
        )
    )

    assert proposal is None
    assert reasoner.last_error == "navimind_action_not_allowed"


def test_navimind_reasoner_rejects_task_id_mismatch():
    def opener(request, timeout):
        return _Response(
            {
                "version": "1",
                "task_id": "different-task",
                "status": "done",
                "rationale": "Done.",
                "confidence": 1.0,
                "action": None,
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
            request_message="Zakończ",
            intent="computer_use",
        )
    )

    assert proposal is None
    assert reasoner.last_error == "navimind_task_id_mismatch"
