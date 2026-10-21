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


class NonExecutingControlLoop:
    """Dependency probe that fails if configuration advances into GUI work."""

    def __init__(self):
        self.observe_calls = 0
        self.run_calls = 0

    def observe_scene(self):
        self.observe_calls += 1
        raise AssertionError("Configuration must not observe the environment.")

    def run(self, *, plan, context):
        self.run_calls += 1
        raise AssertionError("Configuration must not execute a GUI plan.")


class NonExecutingOrchestrator:
    def __init__(self):
        self.prepare_calls = 0

    def prepare(self, *args, **kwargs):
        self.prepare_calls += 1
        raise AssertionError("Configuration must not invoke the planner.")


def test_runtime_explicitly_configures_windowhub_host_without_gui_side_effects(tmp_path):
    control = NonExecutingControlLoop()
    orchestrator = NonExecutingOrchestrator()
    runtime = AgentRuntime(orchestrator=orchestrator, control_loop=control)

    host = runtime.configure_windowhub_resumable_tasks(
        repository=TaskCheckpointRepository(tmp_path),
    )

    checkpoint = TaskCheckpoint(
        "runtime-windowhub-config",
        "Create a WindowHub draft offer",
        max_reasoning_calls=3,
    )
    assert runtime.start_resumable_task(checkpoint) == checkpoint
    assert runtime.get_resumable_task(checkpoint.task_id) == checkpoint
    assert runtime.resumable_task_service is host.service
    assert host.control_loop is control
    assert host.orchestrator is orchestrator
    assert control.observe_calls == 0
    assert control.run_calls == 0
    assert orchestrator.prepare_calls == 0


def test_runtime_refuses_windowhub_configuration_without_explicit_control_loop():
    runtime = AgentRuntime()
    try:
        runtime.configure_windowhub_resumable_tasks()
    except RuntimeError as exc:
        assert "explicitly configured control loop" in str(exc)
    else:
        raise AssertionError("WindowHub resumable tasks must require an explicit control loop.")

    assert runtime.resumable_task_service is None
