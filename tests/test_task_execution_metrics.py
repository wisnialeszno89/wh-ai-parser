from types import SimpleNamespace

import pytest

from app.agent.agent_request import AgentRequest
from app.agent.reasoning.reasoning_action import ReasoningAction
from app.agent.reasoning.reasoning_proposal import ReasoningProposal
from app.agent.reasoning.task_reasoner import TaskReasoner
from app.agent.runtime.agent_orchestrator import AgentOrchestrator
from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime.task_execution_metrics import TaskExecutionMetrics


class MetricsReasoner(TaskReasoner):
    def __init__(self, done_on_call=2):
        self.calls = 0
        self.done_on_call = done_on_call

    def reason(self, context):
        self.calls += 1

        if self.calls >= self.done_on_call:
            return ReasoningProposal(
                actions=(),
                rationale="Goal complete.",
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


class MetricsControlLoop:
    def __init__(self):
        self.calls = 0

    def observe_scene(self):
        return None

    def run(self, *, plan, context):
        self.calls += 1
        return SimpleNamespace(
            success=True,
            requires_manual_review=False,
            stopped=False,
            executed_actions=len(plan.steps),
            failed_actions=0,
        )


def test_autonomous_run_exposes_operational_task_metrics():
    reasoner = MetricsReasoner()
    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(task_reasoner=reasoner),
        control_loop=MetricsControlLoop(),
    )

    result = runtime.run_autonomous(
        AgentRequest(
            message="Wykonaj dwa kroki",
            metadata={"disable_learned_workflow_replay": True},
        ),
        max_steps=5,
        max_reasoning_calls=2,
    )

    metrics = result.execution_metrics

    assert result.completed is True
    assert metrics.cycles == 2
    assert metrics.executed_actions == 1
    assert metrics.successful_actions == 1
    assert metrics.failed_actions == 0
    assert metrics.confirmations_requested == 0
    assert metrics.elapsed_seconds >= 0
    assert metrics.actions_per_cycle == pytest.approx(0.5)

    payload = metrics.to_payload()
    assert payload["executed_actions"] == 1
    assert payload["actions_per_cycle"] == pytest.approx(0.5)


def test_task_execution_metrics_rejects_inconsistent_action_counts():
    with pytest.raises(
        ValueError,
        match="successful_actions \+ failed_actions cannot exceed executed_actions",
    ):
        TaskExecutionMetrics(
            executed_actions=1,
            successful_actions=1,
            failed_actions=1,
        )
