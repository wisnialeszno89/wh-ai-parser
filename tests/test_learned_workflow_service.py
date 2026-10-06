from types import SimpleNamespace

from app.agent.agent_request import AgentRequest
from app.agent.learning.learned_workflow import LearnedWorkflow
from app.agent.learning.learned_workflow_replayer import (
    LearnedWorkflowReplayResult,
    LearnedWorkflowReplayer,
)
from app.agent.learning.learned_workflow_service import (
    LearnedWorkflowService,
)
from app.agent.learning.workflow_memory_store import WorkflowMemoryStore


def _workflow():
    return LearnedWorkflow(
        workflow_id="wf-1",
        name="Dodanie okna",
        application="WindowHub",
        trigger="dodaj nowe okno",
        steps=(
            SimpleNamespace(),
        ),
    )


class FakeReplayerControlLoop:
    pass


def test_service_resolves_exact_trigger_and_replays(monkeypatch):
    workflow = _workflow()
    store = WorkflowMemoryStore(workflows=(workflow,))
    replay_result = LearnedWorkflowReplayResult(
        workflow=workflow,
        success=True,
        completed_steps=1,
        total_steps=1,
        control_loop_result=None,
    )

    def fake_replay(self, workflow, *, request_message):
        assert request_message == "dodaj nowe okno"
        return replay_result

    monkeypatch.setattr(
        LearnedWorkflowReplayer,
        "replay",
        fake_replay,
    )

    service = LearnedWorkflowService(
        memory_store=store,
        control_loop=FakeReplayerControlLoop(),
        min_score=0.99,
    )

    result = service.execute(
        AgentRequest(message="dodaj nowe okno"),
        application="WindowHub",
    )

    assert result is not None
    assert result.match.workflow.workflow_id == "wf-1"
    assert result.match.score == 1.0
    assert result.replay is replay_result


def test_service_returns_none_without_match():
    store = WorkflowMemoryStore(workflows=(_workflow(),))
    service = LearnedWorkflowService(
        memory_store=store,
        control_loop=FakeReplayerControlLoop(),
    )

    assert service.execute(
        AgentRequest(message="zrob cos innego"),
        application="WindowHub",
    ) is None
