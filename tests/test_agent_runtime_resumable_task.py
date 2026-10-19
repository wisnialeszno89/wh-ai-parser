from dataclasses import replace
from types import SimpleNamespace

from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime.resumable_task import Execution, PlanDecision, ResumableTaskRunner, TaskCheckpoint, TaskStatus, Verification
from app.agent.runtime.resumable_task_repository import TaskCheckpointRepository
from app.agent.runtime.resumable_task_service import ResumableTaskService


class CompletingRunner(ResumableTaskRunner):
    def __init__(self):
        super().__init__(
            observe=lambda: SimpleNamespace(
                observation=SimpleNamespace(
                    state=SimpleNamespace(
                        active_application="WindowHub",
                        active_window_title="WindowHub",
                    )
                ),
                elements=(),
                metadata={},
            ),
            plan_next=lambda state, scene: PlanDecision(complete=True),
            execute_action=lambda action, scene, validation: Execution(False, False, "unused"),
            verify_action=lambda action, execution, scene: Verification(False),
            verify_final_state=lambda state, scene: Verification(True, evidence=({"verified": True},)),
        )


def test_agent_runtime_exposes_explicit_checkpoint_lifecycle(tmp_path):
    service = ResumableTaskService(
        repository=TaskCheckpointRepository(tmp_path),
        runner_factory=lambda state: CompletingRunner(),
    )
    runtime = AgentRuntime(resumable_task_service=service)
    initial = TaskCheckpoint("runtime-session", "Create a WindowHub draft", max_reasoning_calls=3)

    assert runtime.start_resumable_task(initial) == initial
    assert runtime.get_resumable_task("runtime-session") == initial
    advanced = runtime.advance_resumable_task("runtime-session")
    assert advanced.status == TaskStatus.COMPLETED
    assert advanced.final_evidence == ({"verified": True},)
    assert runtime.get_resumable_task("runtime-session").status == TaskStatus.COMPLETED


def test_runtime_without_explicit_resumable_service_fails_closed():
    runtime = AgentRuntime()
    try:
        runtime.advance_resumable_task("any")
    except RuntimeError as exc:
        assert "not configured" in str(exc)
    else:
        raise AssertionError("Runtime must not silently create an unconfigured task service.")
