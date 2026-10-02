from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.environment.environment_state import EnvironmentState
from app.agent.environment.fake_environment import FakeEnvironment
from app.agent.execution.execution_engine import ExecutionEngine
from app.agent.execution.execution_result import ExecutionResult
from app.agent.execution.executor_registry import ExecutorRegistry
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.reasoning.openai_plan_reasoner import (
    OpenAIPlanReasoner,
    OpenAIPlanReasonerConfig,
    _OpenAIReasoningAction,
    _OpenAIReasoningProposal,
)
from app.agent.runtime.default_agent_control_loop import (
    create_default_agent_control_loop,
)
from app.agent.runtime.execution_context import ExecutionContext
from app.agent.verification.expected_outcome import ExpectedOutcome
from app.agent.verification.verification_result import (
    VerificationResult,
)


class ParsedResponse:
    def __init__(self, parsed):
        self.output_parsed = parsed


class FakeResponses:
    def __init__(self, parsed):
        self.parsed = parsed
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return ParsedResponse(self.parsed)


class FakeClient:
    def __init__(self, parsed):
        self.responses = FakeResponses(parsed)


class RecordingExecutor:
    def __init__(self):
        self.executed_actions = []

    def supports(self, action):
        return True

    def execute(self, action, context):
        self.executed_actions.append(action.name)
        return ExecutionResult(
            action_name=action.name,
            success=True,
            message="Execution succeeded.",
        )


class StaticExpectationResolver:
    def resolve(self, action, context):
        return ExpectedOutcome(
            description="Expected semantic recovery state."
        )


class SequencedOutcomeVerifier:
    def __init__(self):
        self.calls = 0

    def verify(self, expected, scene):
        self.calls += 1

        if self.calls == 1:
            return VerificationResult(
                verified=False,
                reason="Expected element was not found.",
                confidence=0.9,
                metadata={
                    "expected_label": "Zapisz",
                    "found": False,
                },
            )

        return VerificationResult(
            verified=True,
            reason="Expected recovery state reached.",
            confidence=0.95,
        )


def create_context():
    return ExecutionContext(
        request=AgentRequest(
            message=(
                "Przygotuj ofertę i odzyskaj workflow "
                "po nieudanej weryfikacji."
            ),
        ),
    )


def create_plan():
    return ActionPlan(
        intent=AgentIntent.CREATE_QUOTE,
        steps=(
            ActionStep(
                index=1,
                action=AgentAction(
                    name="failed_action",
                    description="Prepare the quotation workflow.",
                ),
            ),
        ),
        confidence=1.0,
    )


def test_openai_reasoner_is_wired_into_default_control_loop():
    parsed = _OpenAIReasoningProposal(
        actions=(
            _OpenAIReasoningAction(
                name="refresh_current_context",
                description=(
                    "Refresh the semantic context before "
                    "continuing the quotation workflow."
                ),
            ),
        ),
        rationale=(
            "The expected element was not found, so refresh "
            "semantic context before continuing."
        ),
        confidence=0.84,
        requires_manual_review=False,
    )

    client = FakeClient(parsed)

    reasoner = OpenAIPlanReasoner(
        config=OpenAIPlanReasonerConfig(
            api_key="test-key",
            model="gpt-5.6-luna",
        ),
        client=client,
    )

    environment = FakeEnvironment(
        state=EnvironmentState(
            active_application="TestApp",
            active_window_title="Test Window",
            screen_width=1920,
            screen_height=1080,
        ),
    )

    executor = RecordingExecutor()

    loop = create_default_agent_control_loop(
        environment=environment,
        execution_engine=ExecutionEngine(
            ExecutorRegistry(
                executors=(executor,),
            ),
        ),
        plan_reasoner=reasoner,
        max_replans=1,
    )

    loop.verification_loop.expectation_resolver = (
        StaticExpectationResolver()
    )
    loop.verification_loop.outcome_verifier = (
        SequencedOutcomeVerifier()
    )
    loop.verification_loop.max_attempts = 1

    result = loop.run(
        create_plan(),
        create_context(),
    )

    assert result.success is True
    assert result.replanned_actions == 1

    assert executor.executed_actions == [
        "failed_action",
        "refresh_current_context",
    ]

    assert len(client.responses.calls) == 1

    call = client.responses.calls[0]

    assert "execution_runtime" not in call["input"]
    assert "TO-0004" not in call["input"]
    assert "mouse" not in call["input"].casefold()

    assert call["text_format"].__name__ == (
        "_OpenAIReasoningProposal"
    )
