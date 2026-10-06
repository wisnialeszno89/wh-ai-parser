from app.agent.learning.learned_workflow import LearnedWorkflow
from app.agent.learning.semantic_snapshot import SemanticSnapshot
from app.agent.learning.workflow_memory_store import WorkflowMemoryStore
from app.agent.learning.workflow_repository import WorkflowRepository


def _workflow(workflow_id="wf-1"):
    snapshot = SemanticSnapshot(
        application="WindowHub",
        window_title="Okna -",
    )
    return LearnedWorkflow(
        workflow_id=workflow_id,
        name="Dodanie okna",
        application="WindowHub",
        trigger="dodaj nowe okno",
        steps=(),
        metadata={"source": "human_teaching"},
    )


def test_repository_round_trips_workflow(tmp_path):
    repository = WorkflowRepository(tmp_path / "workflows")
    workflow = _workflow()

    path = repository.save(workflow)

    assert path.exists()
    restored = repository.get("wf-1")

    assert restored == workflow
    assert repository.all() == (workflow,)


def test_repository_persists_across_store_instances(tmp_path):
    repository_path = tmp_path / "workflows"
    first = WorkflowMemoryStore(
        repository=WorkflowRepository(repository_path),
        load_persisted=False,
    )
    workflow = _workflow()
    first.save(workflow)

    second = WorkflowMemoryStore(
        repository=WorkflowRepository(repository_path),
        load_persisted=True,
    )

    assert second.get("wf-1") == workflow


def test_repository_delete_removes_workflow(tmp_path):
    repository = WorkflowRepository(tmp_path / "workflows")
    repository.save(_workflow())

    assert repository.delete("wf-1") is True
    assert repository.get("wf-1") is None
    assert repository.delete("wf-1") is False
