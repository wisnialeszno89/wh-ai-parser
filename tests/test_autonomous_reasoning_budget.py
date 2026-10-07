from types import SimpleNamespace

import pytest

from app.agent.agent_request import AgentRequest
from app.agent.reasoning.reasoning_action import ReasoningAction
from app.agent.reasoning.reasoning_proposal import ReasoningProposal
from app.agent.reasoning.task_reasoner import TaskReasoner
from app.agent.runtime.agent_orchestrator import AgentOrchestrator
from app.agent.runtime.agent_runtime import AgentRuntime


class BudgetReasoner(TaskReasoner):
    def __init__(self, done_on_call=None):
        self.calls = 0
        self.done_on_call = done_on_call

    def reason(self, context):
        self.calls += 1

        if self.done_on_call == self.calls:
            return ReasoningProposal(
                actions=(),
                rationale="Goal is complete.",
                confidence=0.99,
                status="done",
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
    def __init__(self):
        self.run_calls = 0

    def observe_scene(self):
        return None

    def run(self, *, plan, context):
        self.run_calls += 1
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


def test_autonomous_reasoning_budget_stops_without_a_third_reasoning_call():
    reasoner = BudgetReasoner()
    runtime = create_runtime(reasoner)

    result = runtime.run_autonomous(
        make_request(),
        max_steps=5,
        max_reasoning_calls=2,
    )

    assert result.success is False
    assert result.completed is False
    assert result.requires_manual_review is True
    assert result.stopped is True
    assert result.reason == "reasoning_budget_exhausted"
    assert result.reasoning_calls == 2
    assert reasoner.calls == 2
    assert result.executed_actions == 2


def test_autonomous_reasoning_budget_allows_completion_at_the_limit():
    reasoner = BudgetReasoner(done_on_call=2)
    runtime = create_runtime(reasoner)

    result = runtime.run_autonomous(
        make_request(),
        max_steps=5,
        max_reasoning_calls=2,
    )

    assert result.success is True
    assert result.completed is True
    assert result.requires_manual_review is False
    assert result.stopped is False
    assert result.reason == "task_completed_by_reasoner"
    assert result.reasoning_calls == 2
    assert reasoner.calls == 2


def test_autonomous_reasoning_budget_rejects_non_positive_limit():
    runtime = create_runtime(BudgetReasoner())

    with pytest.raises(
        ValueError,
        match="max_calls must be at least 1.",
    ):
        runtime.run_autonomous(
            make_request(),
            max_reasoning_calls=0,
        )
