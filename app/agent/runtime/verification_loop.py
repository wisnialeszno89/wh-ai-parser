from app.agent.agent_action import AgentAction

from app.agent.environment.environment_adapter import (
    EnvironmentAdapter,
)

from app.agent.execution.execution_engine import (
    ExecutionEngine,
)

from app.agent.runtime.execution_attempt import (
    ExecutionAttempt,
)

from app.agent.runtime.execution_context import (
    ExecutionContext,
)

from app.agent.runtime.execution_loop_result import (
    ExecutionLoopResult,
)

from app.agent.perception.perception_engine import (
    PerceptionEngine,
)

from app.agent.verification.expectation_resolver import (
    ExpectationResolver,
)

from app.agent.verification.outcome_verifier import (
    OutcomeVerifier,
)


class VerificationLoop:
    """
    Controlled action execution feedback loop.

    Flow:

        action
          ->
        execute
          ->
        observe
          ->
        perceive
          ->
        resolve expectation
          ->
        verify outcome
          ->
        success / retry / manual review

    The loop intentionally has a small retry limit.
    It must never repeatedly interact with an environment
    without control.
    """

    def __init__(
        self,
        execution_engine: ExecutionEngine,
        environment: EnvironmentAdapter,
        perception_engine: PerceptionEngine,
        expectation_resolver: ExpectationResolver,
        outcome_verifier: OutcomeVerifier,
        max_attempts: int = 2,
    ) -> None:

        if max_attempts < 1:
            raise ValueError(
                "max_attempts must be at least 1"
            )

        self.execution_engine = (
            execution_engine
        )

        self.environment = environment

        self.perception_engine = (
            perception_engine
        )

        self.expectation_resolver = (
            expectation_resolver
        )

        self.outcome_verifier = (
            outcome_verifier
        )

        self.max_attempts = max_attempts

    def run(
        self,
        action: AgentAction,
        context: ExecutionContext,
    ) -> ExecutionLoopResult:
        """
        Execute and verify one semantic action.
        """

        attempts = []

        for attempt_number in range(
            1,
            self.max_attempts + 1,
        ):

            execution_result = (
                self.execution_engine.execute(
                    action,
                    context,
                )
            )

            expected_outcome = (
                self.expectation_resolver.resolve(
                    action,
                    context,
                )
            )

            verification_result = None

            if execution_result.success:

                observation = (
                    self.environment.observe()
                )

                context.last_observation = (
                    observation
                )

                scene = (
                    self.perception_engine.perceive(
                        observation
                    )
                )

                context.current_scene = scene

                if expected_outcome is not None:

                    verification_result = (
                        self.outcome_verifier.verify(
                            expected_outcome,
                            scene,
                        )
                    )

            attempt = ExecutionAttempt(
                action=action,
                execution_result=execution_result,
                expected_outcome=expected_outcome,
                verification_result=(
                    verification_result
                ),
                attempt_number=attempt_number,
            )

            attempts.append(
                attempt
            )

            if not execution_result.success:

                return ExecutionLoopResult(
                    attempts=tuple(attempts),
                    success=False,
                    requires_manual_review=(
                        execution_result
                        .requires_manual_review
                    ),
                    stopped=True,
                )

            if verification_result is None:

                return ExecutionLoopResult(
                    attempts=tuple(attempts),
                    success=True,
                )

            if verification_result.success:

                return ExecutionLoopResult(
                    attempts=tuple(attempts),
                    success=True,
                )

        return ExecutionLoopResult(
            attempts=tuple(attempts),
            success=False,
            requires_manual_review=True,
            stopped=True,
        )
