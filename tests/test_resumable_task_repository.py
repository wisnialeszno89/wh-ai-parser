import json

import pytest

from app.agent.runtime.resumable_task import TaskAction, TaskCheckpoint, TaskStatus
from app.agent.runtime.resumable_task_repository import TaskCheckpointRepository


def sample_checkpoint():
    action = TaskAction(
        "confirm-save", "click_screen_element", "Zapisz szkic", "scene-hash",
        requires_confirmation=True,
    )
    return TaskCheckpoint(
        task_id="session/quote-1",
        goal="Create a draft WindowHub quotation",
        facts={"width": 1200, "height": 1500},
        required_fields=("width", "height"),
        citations=({"source": "salesperson_request", "excerpt": "1200x1500"},),
        status=TaskStatus.WAITING_FOR_CONFIRMATION,
        pending_action=action,
        scene_fingerprint="scene-hash",
        actions_used=2,
        reasoning_calls=1,
    )


def test_checkpoint_roundtrips_across_repository_instances(tmp_path):
    first = TaskCheckpointRepository(tmp_path)
    checkpoint = sample_checkpoint()
    path = first.save(checkpoint)

    assert path.exists()
    assert path.parent == tmp_path
    assert path.name != checkpoint.task_id
    loaded = TaskCheckpointRepository(tmp_path).get(checkpoint.task_id)
    assert loaded == checkpoint
    assert loaded.pending_action.action_id == "confirm-save"
    assert loaded.citations[0]["excerpt"] == "1200x1500"


def test_checkpoint_filename_is_hashed_and_task_id_cannot_escape_root(tmp_path):
    repository = TaskCheckpointRepository(tmp_path)
    path = repository.path_for("../../outside")
    assert path.parent == tmp_path
    assert path.suffix == ".json"
    with pytest.raises(ValueError, match="must not be empty"):
        repository.path_for("   ")
    with pytest.raises(ValueError, match="too long"):
        repository.path_for("x" * 201)


def test_corrupt_checkpoint_fails_closed(tmp_path):
    repository = TaskCheckpointRepository(tmp_path)
    path = repository.path_for("broken")
    tmp_path.mkdir(parents=True, exist_ok=True)
    path.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        repository.get("broken")


def test_checkpoint_payload_must_be_an_object(tmp_path):
    repository = TaskCheckpointRepository(tmp_path)
    path = repository.path_for("broken")
    tmp_path.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        repository.get("broken")


def test_missing_checkpoint_and_delete_are_idempotent(tmp_path):
    repository = TaskCheckpointRepository(tmp_path)
    assert repository.get("missing") is None
    assert repository.delete("missing") is False
    repository.save(sample_checkpoint())
    assert repository.delete("session/quote-1") is True
    assert repository.get("session/quote-1") is None
