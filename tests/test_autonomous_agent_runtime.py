from types import SimpleNamespace

from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.reasoning.reasoning_action import ReasoningAction
from app.agent.reasoning.knowledge_context import (
    KnowledgeContext,
    KnowledgeFact,
    KnowledgeSource,
)
from app.agent.reasoning.reasoning_proposal import ReasoningProposal
from app.agent.reasoning.reasoning_task_planner import ReasoningTaskPlanner
from app.agent.reasoning.task_planning_context import TaskPlanningContext
from app.agent.reasoning.task_reasoner import TaskReasoner
from app.agent.runtime.agent_orchestrator import AgentOrchestrator
from app.agent.runtime.agent_runtime import AgentRuntime


class SequenceReasoner(TaskReasoner):
    def __init__(self):
        self.contexts = []
        self.calls = 0

    def reason(self, context):
        self.contexts.append(context)
        self.calls += 1

        if self.calls == 1:
            return ReasoningProposal(
                actions=(
                    ReasoningAction(
                        name="click_screen_element",
                        description="Click the next visible control.",
                        target="NEXT",
                    ),
                ),
                rationale="Advance the visible workflow.",
                confidence=0.95,
            )

        return ReasoningProposal(
            actions=(),
            rationale="The requested workflow is visibly complete.",
            confidence=0.98,
            status="done",
        )


class FakeControlLoop:
    def __init__(self):
        self.observe_calls = 0
        self.run_calls = 0
        self.plans = []

    def observe_scene(self):
        self.observe_calls += 1
        return None

    def run(self, *, plan, context):
        self.run_calls += 1
        self.plans.append(plan)
        return SimpleNamespace(
            success=True,
            requires_manual_review=False,
            stopped=False,
            executed_actions=len(plan.steps),
        )


def test_reasoning_task_planner_accepts_explicit_done_state():
    reasoner = SequenceReasoner()
    planner = ReasoningTaskPlanner(reasoner)

    context = TaskPlanningContext(
        request_message="Otwórz następną sekcję",
        intent=AgentIntent.EXECUTE_IN_WH.value,
        capability_name="WH_WINDOW",
        capability_description="Controlled WindowHub execution.",
        skill_name="WHWindowSkill",
    )

    planner.plan(context=context)
    plan = planner.plan(context=context)

    assert plan is not None
    assert plan.completed is True
    assert plan.steps == ()


def test_runtime_runs_one_action_then_reobserves_and_reasons_again():
    reasoner = SequenceReasoner()
    control_loop = FakeControlLoop()

    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=reasoner,
        ),
        control_loop=control_loop,
    )

    result = runtime.run_autonomous(
        AgentRequest(
            message="Otwórz następną sekcję",
        ),
        max_steps=5,
    )

    assert result.success is True
    assert result.completed is True
    assert result.requires_manual_review is False
    assert result.stopped is False
    assert result.reason == "task_completed_by_reasoner"

    assert len(result.step_results) == 2
    assert control_loop.run_calls == 2
    assert len(control_loop.plans[0].steps) == 1
    assert control_loop.plans[0].completed is False
    assert control_loop.plans[1].completed is True
    assert control_loop.plans[1].steps == ()
    assert reasoner.calls == 2
    assert control_loop.observe_calls == 2


def test_autonomous_unknown_intent_enters_generic_computer_use_reasoning():
    reasoner = SequenceReasoner()
    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=reasoner,
        ),
        control_loop=FakeControlLoop(),
    )

    result = runtime.run_autonomous(
        AgentRequest(message="Zmień bieżący widok na następny"),
        max_steps=2,
    )

    assert result.success is True
    assert reasoner.calls == 2
    assert reasoner.contexts[0].intent == AgentIntent.COMPUTER_USE.value
    assert reasoner.contexts[0].capability_name == "COMPUTER_USE"
    assert reasoner.contexts[0].skill_name == "ComputerUseSkill"


class ResearchMemoryReasoner(TaskReasoner):
    def __init__(self):
        self.contexts = []
        self.calls = 0

    def reason(self, context):
        self.contexts.append(context)
        self.calls += 1

        knowledge = KnowledgeContext(
            status="complete",
            query="produkt specyfikacja",
            sources=(
                KnowledgeSource(
                    source_id="web-1",
                    title="Manufacturer documentation",
                    url="https://example.com/spec",
                ),
            ),
            facts=(
                KnowledgeFact(
                    fact_id="synth-fact-1",
                    claim="Product X supports triple glazing.",
                    source_ids=("web-1",),
                    confidence=0.84,
                    relevance=0.91,
                    kind="retrieved_evidence",
                ),
            ),
            limitations=("Not independently verified.",),
        )

        if self.calls == 1:
            return ReasoningProposal(
                actions=(
                    ReasoningAction(
                        name="click_screen_element",
                        description="Open the visible product section.",
                        target="NEXT",
                    ),
                ),
                rationale="Use research-backed context.",
                confidence=0.91,
                metadata={
                    "external_knowledge": knowledge.to_payload(),
                },
            )

        return ReasoningProposal(
            actions=(),
            rationale="Research context persisted into the next cycle.",
            confidence=0.97,
            status="done",
        )


def test_autonomous_runtime_persists_external_knowledge_between_cycles():
    reasoner = ResearchMemoryReasoner()
    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            task_reasoner=reasoner,
        ),
        control_loop=FakeControlLoop(),
    )

    result = runtime.run_autonomous(
        AgentRequest(message="Sprawdź produkt"),
        max_steps=3,
    )

    assert result.success is True
    assert result.completed is True
    assert reasoner.calls == 2
    assert reasoner.contexts[1].external_knowledge is not None
    assert reasoner.contexts[1].external_knowledge.status == "complete"
    assert (
        reasoner.contexts[1].external_knowledge.facts[0].fact_id
        == "synth-fact-1"
    )
