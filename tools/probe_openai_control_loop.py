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
)
from app.agent.reasoning.plan_reasoner import PlanReasoner
from app.agent.reasoning.reasoning_proposal import ReasoningProposal
from app.agent.runtime.default_agent_control_loop import (
    create_default_agent_control_loop,
)
from app.agent.runtime.execution_context import ExecutionContext
from app.agent.verification.expected_outcome import ExpectedOutcome
from app.agent.verification.verification_result import (
    VerificationResult,
)


class RecordingReasoner(PlanReasoner):
    def __init__(self, delegate):
        self.delegate = delegate
        self.last_proposal = None

    def reason(self, context):
        self.last_proposal = self.delegate.reason(context)
        return self.last_proposal


class DryRunSemanticExecutor:
    """Records semantic actions only; never touches a GUI."""

    def __init__(self):
        self.executed_actions = []

    def supports(self, action):
        return True

    def execute(self, action, context):
        self.executed_actions.append(action.name)
        return ExecutionResult(
            action_name=action.name,
            success=True,
            message="DRY_RUN semantic action accepted.",
        )


class StaticExpectationResolver:
    def resolve(self, action, context):
        return ExpectedOutcome(
            description="Expected semantic recovery state.",
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
                    name="prepare_quote",
                    description=(
                        "Prepare the quotation workflow "
                        "for controlled execution."
                    ),
                ),
            ),
        ),
        confidence=1.0,
    )


def main() -> int:
    reasoner = RecordingReasoner(
        OpenAIPlanReasoner()
    )

    environment = FakeEnvironment(
        state=EnvironmentState(
            active_application="UniversalAgent-DryRun",
            active_window_title="Quote Recovery Test",
            screen_width=1920,
            screen_height=1080,
        ),
    )

    executor = DryRunSemanticExecutor()

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

    print("OpenAI control-loop probe")
    print("=========================")

    proposal = reasoner.last_proposal

    if proposal is None:
        print(
            "No reasoning proposal was returned. "
            "The loop failed closed."
        )
    else:
        print(
            f"reasoning_confidence={proposal.confidence}"
        )
        print(
            "requires_manual_review="
            f"{proposal.requires_manual_review}"
        )
        print(f"rationale={proposal.rationale}")

        for index, action in enumerate(
            proposal.actions,
            start=1,
        ):
            print(
                f"proposal_{index}={action.name} | "
                f"{action.description} | "
                f"confirmation={action.requires_confirmation}"
            )

    print(
        f"control_loop_success={result.success}"
    )
    print(
        f"replanned_actions={result.replanned_actions}"
    )
    print(
        f"requires_manual_review="
        f"{result.requires_manual_review}"
    )
    print(
        f"stopped={result.stopped}"
    )
    print(
        "executed_actions="
        f"{executor.executed_actions}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
