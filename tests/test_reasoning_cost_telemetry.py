import pytest

from app.agent.adapters.browser_adapter import BrowserPage
from app.agent.reasoning.navimind_task_reasoner import (
    NaviMindTaskReasoner,
    NaviMindTaskReasonerConfig,
)
from app.agent.reasoning.task_planning_context import TaskPlanningContext
from app.agent.runtime.reasoning_usage import (
    ReasoningCostTracker,
    ReasoningUsage,
    estimate_openai_cost_usd,
)


class Response:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        import json

        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_openai_usage_estimate_accounts_for_cached_input():
    cost = estimate_openai_cost_usd(
        model="gpt-4.1-mini",
        input_tokens=1_000,
        cached_input_tokens=400,
        output_tokens=250,
    )

    assert cost == pytest.approx(0.00068)


def test_unknown_model_keeps_cost_explicitly_unpriced():
    usage = ReasoningUsage.from_payload(
        {
            "provider": "openai",
            "model": "future-model",
            "input_tokens": 100,
            "cached_input_tokens": 20,
            "output_tokens": 30,
            "total_tokens": 130,
            "reasoning_tokens": 0,
        }
    )

    assert usage.total_tokens == 130
    assert usage.uncached_input_tokens == 80
    assert usage.estimated_cost_usd is None


def test_reasoning_cost_tracker_aggregates_usage():
    tracker = ReasoningCostTracker()
    tracker.record(
        ReasoningUsage.from_payload(
            {
                "provider": "openai",
                "model": "gpt-4.1-mini",
                "input_tokens": 1_000,
                "cached_input_tokens": 0,
                "output_tokens": 100,
                "total_tokens": 1_100,
                "reasoning_tokens": 0,
            }
        )
    )
    tracker.record(
        ReasoningUsage.from_payload(
            {
                "provider": "openai",
                "model": "gpt-4.1-mini",
                "input_tokens": 500,
                "cached_input_tokens": 200,
                "output_tokens": 50,
                "total_tokens": 550,
                "reasoning_tokens": 0,
            }
        )
    )

    summary = tracker.summary()

    assert summary.calls == 2
    assert summary.input_tokens == 1_500
    assert summary.cached_input_tokens == 200
    assert summary.uncached_input_tokens == 1_300
    assert summary.output_tokens == 150
    assert summary.total_tokens == 1_650
    assert summary.reasoning_tokens == 0
    assert summary.models == ("gpt-4.1-mini",)
    assert summary.estimated_cost_usd == pytest.approx(0.000605)


def test_navimind_usage_is_preserved_on_semantic_reasoning_proposal():
    captured = {}

    def opener(request, timeout):
        import json

        captured["body"] = json.loads(request.data.decode("utf-8"))
        return Response(
            {
                "version": "1",
                "task_id": captured["body"]["task_id"],
                "status": "continue",
                "rationale": "Use the visible control.",
                "confidence": 0.95,
                "action": {
                    "name": "browser_click",
                    "description": "Click the visible control.",
                    "target": "Dalej",
                    "value": None,
                },
                "requires_manual_review": False,
                "usage": {
                    "provider": "openai",
                    "model": "gpt-4.1-mini",
                    "input_tokens": 1_000,
                    "output_tokens": 100,
                    "total_tokens": 1_100,
                    "cached_input_tokens": 400,
                    "reasoning_tokens": 0,
                },
            }
        )

    page = BrowserPage(
        url="https://example.com",
        title="Example",
        text="Dalej",
        elements=(),
    )
    context = TaskPlanningContext(
        request_message="Kliknij Dalej",
        intent="computer_use",
        session_id="usage-session",
        browser_page=page,
    )

    reasoner = NaviMindTaskReasoner(
        config=NaviMindTaskReasonerConfig(
            url="http://localhost:3000/api/agent/task",
        ),
        opener=opener,
    )
    proposal = reasoner.reason(context)

    assert proposal is not None
    assert reasoner.last_usage is not None
    assert reasoner.last_usage.input_tokens == 1_000
    assert reasoner.last_usage.cached_input_tokens == 400
    assert reasoner.last_usage.estimated_cost_usd == pytest.approx(
        0.00068
    )
    assert proposal.metadata["reasoning_usage"]["output_tokens"] == 100
