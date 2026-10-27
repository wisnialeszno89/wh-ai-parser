from app.agent.adapters.pdf_document_adapter import PdfDocumentAdapter
from app.agent.adapters.pdf_ingestion_service import PdfIngestionService
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



def test_windowhub_runtime_factory_accepts_an_explicit_approved_pdf_ingestion_service(
    monkeypatch,
    tmp_path,
):
    monkeypatch.delenv("NAVIMIND_AGENT_URL", raising=False)
    monkeypatch.delenv("AGENT_TASK_REASONING", raising=False)
    approved_root = tmp_path / "approved"
    approved_root.mkdir()
    pdf_service = PdfIngestionService(
        adapter=PdfDocumentAdapter(allowed_roots=(approved_root,)),
    )
    control_loop = NoopControlLoop()

    runtime = module.create_windowhub_agent_runtime(
        control_loop_factory=lambda *, plan_reasoner: control_loop,
        pdf_ingestion_service=pdf_service,
    )

    assert isinstance(runtime, AgentRuntime)
    assert runtime.pdf_ingestion_service is pdf_service
    assert runtime.pdf_source_registry == {}
    assert runtime.resumable_task_service is not None
    assert control_loop.observe_calls == 0
    assert control_loop.run_calls == 0



def test_windowhub_runtime_uses_navimind_without_optional_openai_replanner(monkeypatch):
    monkeypatch.setenv("NAVIMIND_AGENT_URL", "https://navimind.example.invalid/agent")
    monkeypatch.setenv("NAVIMIND_AGENT_SECRET", "test-secret-not-used-for-network")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AGENT_TASK_REASONING", raising=False)

    control_loop = NoopControlLoop()
    configured = {}

    def control_loop_factory(*, plan_reasoner):
        configured["plan_reasoner"] = plan_reasoner
        return control_loop

    runtime = module.create_windowhub_agent_runtime(
        control_loop_factory=control_loop_factory,
    )

    assert runtime.orchestrator.task_planner is not None
    assert configured["plan_reasoner"] is None
    assert runtime.resumable_task_service is not None
    assert control_loop.observe_calls == 0
    assert control_loop.run_calls == 0
