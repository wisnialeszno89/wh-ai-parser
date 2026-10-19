from dataclasses import replace

import pytest

from app.agent.runtime.resumable_task import Execution, PlanDecision, ResumableTaskRunner, TaskAction, TaskCheckpoint, TaskStatus, Verification
from app.agent.runtime.resumable_task_repository import TaskCheckpointRepository
from app.agent.runtime.resumable_task_service import ResumableTaskService


class OneStepRunner(ResumableTaskRunner):
    def __init__(self):
        super().__init__(
            observe=lambda: object(),
            plan_next=lambda state, scene: PlanDecision(),
            execute_action=lambda action, scene, validation: Execution(False, False, "unused"),
            verify_action=lambda action, execution, scene: Verification(False),
            verify_final_state=lambda state, scene: Verification(False),
        )

    def advance(self, state):
        return replace(state, reasoning_calls=state.reasoning_calls + 1)


def make_service(tmp_path):
    return ResumableTaskService(
        repository=TaskCheckpointRepository(tmp_path),
        runner_factory=lambda state: OneStepRunner(),
    )


def test_create_prevents_accidental_task_id_overwrite(tmp_path):
    service = make_service(tmp_path)
    checkpoint = TaskCheckpoint("t", "create a draft", max_reasoning_calls=3)
    assert service.create(checkpoint) == checkpoint
    with pytest.raises(FileExistsError):
        service.create(checkpoint)


def test_advance_persists_updated_checkpoint_for_next_process(tmp_path):
    service = make_service(tmp_path)
    service.create(TaskCheckpoint("t", "create a draft", max_reasoning_calls=3))
    assert service.advance("t").reasoning_calls == 1

    reloaded = ResumableTaskService(
        repository=TaskCheckpointRepository(tmp_path),
        runner_factory=lambda state: OneStepRunner(),
    )
    assert reloaded.get("t").reasoning_calls == 1
    assert reloaded.advance("t").reasoning_calls == 2


def test_service_preserves_confirmation_and_requires_explicit_submission_approval(tmp_path):
    service = make_service(tmp_path)
    checkpoint = TaskCheckpoint(
        "t", "send offer",
        status=TaskStatus.WAITING_FOR_CONFIRMATION,
        pending_action=TaskAction(
            "send", "click_screen_element", "Wyślij ofertę", "scene-1", submission=True
        ),
    )
    service.create(checkpoint)
    with pytest.raises(ValueError, match="explicit"):
        service.approve_pending_action("t")
    approved = service.approve_pending_action("t", approve_submission=True)
    assert approved.status == TaskStatus.READY
    assert approved.draft_only is False


def test_unknown_checkpoint_operations_raise_clear_errors(tmp_path):
    service = make_service(tmp_path)
    with pytest.raises(KeyError, match="No checkpoint"):
        service.advance("unknown")
    with pytest.raises(KeyError, match="No checkpoint"):
        service.supply_facts("unknown", {"width": 1200})
