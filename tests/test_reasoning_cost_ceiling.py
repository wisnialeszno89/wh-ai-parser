from types import SimpleNamespace

import pytest

from app.agent.agent_request import AgentRequest
from app.agent.reasoning.reasoning_action import ReasoningAction
from app.agent.reasoning.reasoning_proposal import ReasoningProposal
from app.agent.reasoning.task_reasoner import TaskReasoner
from app.agent.runtime.agent_orchestrator import AgentOrchestrator
from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime.reasoning_usage import ReasoningUsage


class CostLimitedReasoner(TaskReasoner):
    def __init__(self):
        self.calls = 0
        self.last_usage = None

    def reason(self, context):
        self.calls += 1
        self.last_usage = ReasoningUsage(
            provider="openai",
            model="gpt-4.1-mini",
            input_tokens=1_000,
            output_tokens=100,
            total_tokens=1_100,
            cached_input_tokens=400,
            reasoning_tokens=0,
            estimated_cost_usd=0.00044,
        )
        return ReasoningProposal(
            actions=(
                ReasoningAction(
                    name="click_screen_element",
                    description="Click the next visible control.",
                    target="NEXT",
                ),
            ),
            rationale="Advance one workflow step.",
            confidence=0.95,
        )


class FakeControlLoop:
    def run(self, *, plan, context):
        return SimpleNamespace(
            success=True,
            requires_manual_review=False,
            stopped=False,
            executed_actions=len(plan.steps),
        )


def create_runtime(reasoner):
    return AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=reasoner,
        ),
        control_loop=FakeControlLoop(),
    )


def make_request():
    return AgentRequest(
        message="Otwórz następną sekcję",
        metadata={
            "disable_learned_workflow_replay": True,
        },
    )


def test_autonomous_cost_ceiling_stops_before_next_reasoning_call():
    reasoner = CostLimitedReasoner()
    runtime = create_runtime(reasoner)

    result = runtime.run_autonomous(
        make_request(),
        max_steps=5,
        max_reasoning_calls=8,
        max_estimated_reasoning_cost_usd=0.0004,
    )

    assert result.success is False
    assert result.completed is False
    assert result.requires_manual_review is True
    assert result.stopped is True
    assert result.reason == "reasoning_cost_limit_reached"
    assert result.reasoning_calls == 1
    assert result.executed_actions == 1
    assert reasoner.calls == 1
    assert result.reasoning_cost.estimated_cost_usd == pytest.approx(
        0.00044
    )


@pytest.mark.parametrize("limit", [0, -0.001])
def test_autonomous_cost_ceiling_rejects_non_positive_limit(limit):
    runtime = create_runtime(CostLimitedReasoner())

    with pytest.raises(
        ValueError,
        match="max_estimated_reasoning_cost_usd must be greater than 0.",
    ):
        runtime.run_autonomous(
            make_request(),
            max_estimated_reasoning_cost_usd=limit,
        )
