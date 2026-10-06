from types import SimpleNamespace

from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.learning.agent_mode import AgentMode
from app.agent.learning.learned_workflow import (
    LearnedAction,
    LearnedWorkflow,
    LearnedWorkflowStep,
)
from app.agent.learning.semantic_snapshot import SemanticSnapshot
from app.agent.learning.workflow_memory_store import WorkflowMemoryStore
from app.agent.runtime.agent_orchestrator import AgentOrchestrator
from app.agent.runtime.agent_runtime import AgentRuntime


def _scene():
    return SimpleNamespace(
        observation=SimpleNamespace(
            state=SimpleNamespace(
                active_application="WindowHub",
                active_window_title="Okna -",
            )
        ),
        active_document=None,
        elements=(),
    )


def _workflow():
    snapshot = SemanticSnapshot(
        application="WindowHub",
        window_title="Okna -",
    )
    return LearnedWorkflow(
        workflow_id="wf-learned",
        name="Dodanie okna",
        application="WindowHub",
        trigger="dodaj nowe okno",
        steps=(
            LearnedWorkflowStep(
                index=1,
                action=LearnedAction(
                    name="click_screen_element",
                    target="Dodaj",
                ),
                before=snapshot,
                after=snapshot,
            ),
        ),
    )


class FakeControlLoop:
    def __init__(self):
        self.scene = _scene()
        self.run_calls = 0

    def observe_scene(self):
        return self.scene

    def run(self, *, plan, context):
        self.run_calls += 1
        return SimpleNamespace(
            success=True,
            requires_manual_review=False,
            stopped=False,
            step_results=(),
        )


def test_runtime_dispatches_exact_learned_workflow_before_generic_planning():
    control_loop = FakeControlLoop()
    workflow = _workflow()

    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(
            workflow_memory_store=WorkflowMemoryStore(
                workflows=(workflow,),
                load_persisted=False,
            ),
        ),
        control_loop=control_loop,
    )

    result = runtime.run(
        AgentRequest(
            message="dodaj nowe okno",
            mode=AgentMode.EXECUTE,
        )
    )

    assert result.intent is AgentIntent.OBSERVE_WORKFLOW
    assert result.executed is True
    assert result.requires_manual_review is False
    assert result.control_loop_result.success is True
    assert control_loop.run_calls == 1
    assert result.context.get_value("learned_workflow_id") == "wf-learned"
    assert result.context.get_value("learned_workflow_match_score") == 1.0
