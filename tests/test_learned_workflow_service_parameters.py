from app.agent.agent_request import AgentRequest
from app.agent.learning.learned_workflow import (
    LearnedAction,
    LearnedWorkflow,
    LearnedWorkflowStep,
)
from app.agent.learning.learned_workflow_replayer import LearnedWorkflowReplayResult
from app.agent.learning.learned_workflow_service import LearnedWorkflowService
from app.agent.learning.semantic_snapshot import SemanticSnapshot
from app.agent.learning.workflow_memory_store import WorkflowMemoryStore


def _workflow():
    snapshot = SemanticSnapshot(
        application="WindowHub",
        window_title="Nowe okno",
    )
    return LearnedWorkflow(
        workflow_id="wf-1",
        name="Nowe okno",
        application="WindowHub",
        trigger="dodaj nowe okno",
        steps=(
            LearnedWorkflowStep(
                index=1,
                action=LearnedAction(
                    name="write_text",
                    target="Szerokość",
                    value="1200",
                    value_source="parameter",
                    parameter_name="szerokosc",
                ),
                before=snapshot,
                after=snapshot,
            ),
        ),
    )


class FakeControlLoop:
    pass


def test_service_prefers_explicit_request_parameters(monkeypatch):
    workflow = _workflow()
    store = WorkflowMemoryStore(workflows=(workflow,))

    replay = LearnedWorkflowReplayResult(
        workflow=workflow,
        success=True,
        completed_steps=1,
        total_steps=1,
        control_loop_result=None,
    )
    captured = {}

    def fake_replay(self, workflow, *, request_message, parameters):
        captured["parameters"] = parameters
        return replay

    monkeypatch.setattr(
        "app.agent.learning.learned_workflow_replayer.LearnedWorkflowReplayer.replay",
        fake_replay,
    )

    service = LearnedWorkflowService(
        memory_store=store,
        control_loop=FakeControlLoop(),
        parameter_resolver=lambda request, workflow: {"width": 999},
    )

    result = service.execute(
        AgentRequest(
            message="dodaj nowe okno",
            metadata={"learned_parameters": {"width": 1350}},
        ),
        application="WindowHub",
    )

    assert result.parameters == {"width": 1350}
    assert captured["parameters"] == {"width": 1350}


def test_service_accepts_trigger_prefix_when_all_learned_parameters_resolve(
    monkeypatch,
):
    workflow = _workflow()
    store = WorkflowMemoryStore(workflows=(workflow,))

    replay = LearnedWorkflowReplayResult(
        workflow=workflow,
        success=True,
        completed_steps=1,
        total_steps=1,
        control_loop_result=None,
    )
    captured = {}

    def fake_replay(self, workflow, *, request_message, parameters):
        captured["parameters"] = parameters
        return replay

    monkeypatch.setattr(
        "app.agent.learning.learned_workflow_replayer.LearnedWorkflowReplayer.replay",
        fake_replay,
    )

    service = LearnedWorkflowService(
        memory_store=store,
        control_loop=FakeControlLoop(),
        parameter_resolver=lambda request, workflow: {
            "szerokosc": 1350,
        },
    )

    result = service.execute(
        AgentRequest(
            message="dodaj nowe okno o szerokości 1350",
        ),
        application="WindowHub",
    )

    assert result is not None
    assert result.match.score == 0.92
    assert result.parameters == {"szerokosc": 1350}
    assert captured["parameters"] == {"szerokosc": 1350}
