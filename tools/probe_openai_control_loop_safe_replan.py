from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.agent.agent_action import AgentAction
from app.agent.agent_intent import AgentIntent
from app.agent.agent_request import AgentRequest
from app.agent.environment.environment_state import EnvironmentState
from app.agent.environment.fake_environment import FakeEnvironment
from app.agent.execution.execution_engine import ExecutionEngine
from app.agent.execution.execution_result import ExecutionResult
from app.agent.execution.executor_registry import ExecutorRegistry
from app.agent.perception.interaction_capability import (
    InteractionCapability,
)
from app.agent.perception.perception_provider import PerceptionProvider
from app.agent.perception.screen_element import ScreenElement
from app.agent.perception.semantic_evidence import (
    EvidenceKind,
    EvidenceSource,
    SemanticEvidence,
)
from app.agent.planning.action_plan import ActionPlan
from app.agent.planning.action_step import ActionStep
from app.agent.reasoning.openai_plan_reasoner import (
    OpenAIPlanReasoner,
)
from app.agent.reasoning.plan_reasoner import PlanReasoner
from app.agent.runtime.default_agent_control_loop import (
    create_default_agent_control_loop,
)
from app.agent.runtime.execution_context import ExecutionContext
from app.agent.verification.expected_outcome import ExpectedOutcome
from app.agent.verification.verification_result import (
    VerificationResult,
)


class StaticRecoverySceneProvider(PerceptionProvider):
    """Returns a semantic scene with an explicitly observed recovery option."""

    def perceive(self, observation):
        return (
            ScreenElement(
                kind="button",
                label="Odśwież formularz",
                confidence=0.98,
                interaction_capability=(
                    InteractionCapability.CLICKABLE
                ),
                evidence=(
                    SemanticEvidence(
                        source=EvidenceSource.ACCESSIBILITY,
                        kind=EvidenceKind.LABEL,
                        value="Odśwież formularz",
                        confidence=0.99,
                        element_id="RECOVERY-001",
                    ),
                    SemanticEvidence(
                        source=EvidenceSource.ACCESSIBILITY,
                        kind=(
                            EvidenceKind.INTERACTION_CAPABILITY
                        ),
                        value="clickable",
                        confidence=0.99,
                        element_id="RECOVERY-001",
                    ),
                ),
            ),
            ScreenElement(
                kind="text",
                label="Oferta robocza",
                confidence=0.97,
                interaction_capability=(
                    InteractionCapability.NOT_INTERACTIVE
                ),
                evidence=(
                    SemanticEvidence(
                        source=EvidenceSource.OCR,
                        kind=EvidenceKind.TEXT,
                        value="Oferta robocza",
                        confidence=0.97,
                        element_id="TEXT-001",
                    ),
                ),
            ),
        )


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
                reason=(
                    "Expected save state was not reached, "
                    "but a confirmed refresh control is visible."
                ),
                confidence=0.96,
                metadata={
                    "expected_label": "Zapisz",
                    "found": False,
                    "safe_recovery_available": True,
                    "recovery_label": "Odśwież formularz",
                },
            )

        return VerificationResult(
            verified=True,
            reason="Expected semantic recovery state reached.",
            confidence=0.97,
        )


class RecordingReasoner(PlanReasoner):
    def __init__(self, delegate):
        self.delegate = delegate
        self.last_proposal = None

    def reason(self, context):
        self.last_proposal = self.delegate.reason(context)
        return self.last_proposal


def create_context():
    return ExecutionContext(
        request=AgentRequest(
            message=(
                "Przygotuj ofertę. Jeśli zapis nie zostanie "
                "potwierdzony, użyj wyłącznie bezpiecznej, "
                "odwracalnej możliwości odświeżenia bieżącego "
                "formularza, jeżeli scena ją jednoznacznie "
                "potwierdza."
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
            active_window_title="Quote Recovery Test - Safe Recovery",
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
        perception_providers=(
            StaticRecoverySceneProvider(),
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

    print("OpenAI safe-replan control-loop probe")
    print("====================================")

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
        f"executed_actions={executor.executed_actions}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
