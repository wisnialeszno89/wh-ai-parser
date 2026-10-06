from types import SimpleNamespace

from app.agent.agent_request import AgentRequest
from app.agent.learning.learned_workflow import (
    LearnedAction,
    LearnedWorkflow,
    LearnedWorkflowStep,
)
from app.agent.learning.semantic_snapshot import SemanticSnapshot
from app.agent.learning.workflow_memory_store import WorkflowMemoryStore
from app.agent.memory.agent_memory_store import AgentMemoryStore
from app.agent.runtime.agent_orchestrator import AgentOrchestrator
from app.agent.runtime.agent_runtime import AgentRuntime


def _scene():
    return SimpleNamespace(
        observation=SimpleNamespace(
            state=SimpleNamespace(
                active_application="WindowHub",
                active_window_title="Okna",
            )
        ),
        active_document=None,
        elements=(),
    )


def _workflow():
    snapshot = SemanticSnapshot(
        application="WindowHub",
        window_title="Okna",
    )
    return LearnedWorkflow(
        workflow_id="wf-memory",
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

    def observe_scene(self):
        return self.scene

    def run(self, plan, context):
        return SimpleNamespace(
            success=True,
            requires_manual_review=False,
            stopped=False,
            step_results=(),
        )


def test_runtime_records_learned_workflow_outcome_without_raw_request():
    workflow = _workflow()
    memory = AgentMemoryStore()
    orchestrator = AgentOrchestrator(
        workflow_memory_store=WorkflowMemoryStore(
            workflows=(workflow,),
            load_persisted=False,
        ),
        memory_store=memory,
    )

    runtime = AgentRuntime(
        orchestrator=orchestrator,
        control_loop=FakeControlLoop(),
    )

    result = runtime.run(
        AgentRequest(
            message="dodaj nowe okno",
            mode=__import__(
                "app.agent.learning.agent_mode",
                fromlist=["AgentMode"],
            ).AgentMode.EXECUTE,
        )
    )

    assert result.executed is True
    experiences = memory.all()
    assert len(experiences) == 1
    assert experiences[0].workflow_id == "wf-memory"
    assert experiences[0].outcome == "success"
    assert experiences[0].summary == (
        "Replayed learned workflow 'Dodanie okna'."
    )
    assert "dodaj nowe okno" not in experiences[0].to_payload().__str__()
