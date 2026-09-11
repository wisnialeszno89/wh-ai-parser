from dataclasses import dataclass

from app.agent.agent_action import AgentAction

from app.agent.execution.execution_result import (
    ExecutionResult,
)

from app.agent.verification.expected_outcome import (
    ExpectedOutcome,
)

from app.agent.verification.verification_result import (
    VerificationResult,
)


@dataclass(frozen=True)
class ExecutionAttempt:
    """
    Complete record of one action execution attempt.

    An attempt connects:

    action
        ->
    execution result
        ->
    expected outcome
        ->
    verification result

    This object represents one complete feedback cycle.
    """

    action: AgentAction

    execution_result: ExecutionResult

    expected_outcome: ExpectedOutcome

    verification_result: VerificationResult | None

    attempt_number: int = 1
