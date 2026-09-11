from dataclasses import dataclass

from app.agent.runtime.execution_attempt import (
    ExecutionAttempt,
)


@dataclass(frozen=True)
class ExecutionLoopResult:
    """
    Result of executing one action through the controlled
    execution and verification feedback loop.
    """

    attempts: tuple[ExecutionAttempt, ...]

    success: bool

    requires_manual_review: bool = False

    stopped: bool = False

    @property
    def last_attempt(self) -> ExecutionAttempt | None:
        if not self.attempts:
            return None

        return self.attempts[-1]
