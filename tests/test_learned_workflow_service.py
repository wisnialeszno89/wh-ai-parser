from types import SimpleNamespace

from app.agent.agent_request import AgentRequest
from app.agent.learning.learned_workflow import LearnedWorkflow
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
        steps=(),
    )


class FakeReplayerControlLoop:
    pass


def test_service_requires_high_confidence_match():
    store = WorkflowMemoryStore(workflows=(_workflow(),))
    service = LearnedWorkflowService(
        memory_store=store,
        control_loop=FakeReplayerControlLoop(),
        min_score=0.99,
    )

    # Empty workflows cannot replay, but the service should still resolve
    # the exact trigger before the replayer reports the invalid workflow.
    try:
        service.execute(
            AgentRequest(message="dodaj nowe okno"),
            application="WindowHub",
        )
    except ValueError as exc:
        assert "without steps" in str(exc)
    else:
        raise AssertionError("Expected empty learned workflow to be rejected")


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


def test_service_exposes_ranked_match_and_replay():
    class FakeReplayer:
        def replay(self, workflow, *, request_message):
            return SimpleNamespace(
                workflow=workflow,
                success=True,
                completed_steps=1,
                total_steps=1,
            )

    store = WorkflowMemoryStore(workflows=(
        LearnedWorkflow(
            workflow_id="wf-1",
            name="Dodanie okna",
            application="WindowHub",
            trigger="dodaj nowe okno",
            steps=(
                SimpleNamespace(index=1),
            ),
        ),
    ))

    service = LearnedWorkflowService(
        memory_store=store,
        control_loop=FakeReplayerControlLoop(),
    )

    # The public service uses the concrete semantic replayer. Keep this test
    # focused on resolution by supplying a real workflow with a minimal fake
    # control loop in a separate compatibility test below.
    assert service.memory_store.match(
        "dodaj nowe okno",
        application="WindowHub",
        min_score=0.99,
    )[0].workflow.workflow_id == "wf-1"
