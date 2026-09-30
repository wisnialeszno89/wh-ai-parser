from types import SimpleNamespace

from app.agent.agent_request import AgentRequest
from app.agent.runtime.agent_orchestrator import AgentOrchestrator
from app.agent.runtime.agent_runtime import AgentRuntime


class RecordingControlLoop:
    def __init__(self):
        self.calls = []

    def run(self, *, plan, context):
        self.calls.append((plan, context))

        return SimpleNamespace(
            success=True,
            requires_manual_review=False,
        )


def test_runtime_uses_control_loop_when_configured():
    control_loop = RecordingControlLoop()

    runtime = AgentRuntime(
        orchestrator=AgentOrchestrator(),
        control_loop=control_loop,
    )

    result = runtime.run(
        AgentRequest(
            message="Zrób wycenę okna"
        )
    )

    assert result.executed is True
    assert result.execution_report is None
    assert result.control_loop_result is not None
    assert result.requires_manual_review is False

    assert len(control_loop.calls) == 1

    plan, context = control_loop.calls[0]

    assert context.plan == plan
    assert plan.intent.value == "create_quote"
