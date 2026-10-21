from app.agent.runtime.agent_runtime import AgentRuntime
from app.agent.runtime import windowhub_agent_runtime as module


class NoopControlLoop:
    def __init__(self):
        self.observe_calls = 0
        self.run_calls = 0

    def observe_scene(self):
        self.observe_calls += 1
        raise AssertionError("Runtime factory setup must not observe WindowHub.")

    def run(self, *, plan, context):
        self.run_calls += 1
        raise AssertionError("Runtime factory setup must not execute GUI actions.")


def test_windowhub_runtime_factory_configures_resumable_host_without_side_effects(
    monkeypatch,
):
    monkeypatch.delenv("NAVIMIND_AGENT_URL", raising=False)
    monkeypatch.delenv("AGENT_TASK_REASONING", raising=False)
    control_loop = NoopControlLoop()

    runtime = module.create_windowhub_agent_runtime(
        control_loop_factory=lambda *, plan_reasoner: control_loop,
    )

    assert isinstance(runtime, AgentRuntime)
    assert runtime.control_loop is control_loop
    assert runtime.resumable_task_service is not None
    assert runtime._windowhub_resumable_task_host.service is runtime.resumable_task_service
    assert runtime._windowhub_resumable_task_host.control_loop is control_loop
    assert runtime._windowhub_resumable_task_host.orchestrator is runtime.orchestrator
    assert runtime.orchestrator.application_knowledge["application"] == "WindowHub"
    assert control_loop.observe_calls == 0
    assert control_loop.run_calls == 0
