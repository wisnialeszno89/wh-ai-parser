from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.wh.runtime.error_policy import ErrorAction, WindowHubErrorPolicy


@dataclass(frozen=True)
class ExecutionFailure:
    code: str
    message: str


@dataclass(frozen=True)
class ExecutionOutcome:
    success: bool
    action: ErrorAction | None = None
    error: ExecutionFailure | None = None
    attempts: int = 1


class ControlledExecutor:
    """Executes one WH operation according to deterministic error policy."""

    def __init__(self, policy: WindowHubErrorPolicy | None = None) -> None:
        self.policy = policy or WindowHubErrorPolicy()

    def run(
        self,
        operation: Callable[[], bool],
        error_code: Callable[[Exception], str] | None = None,
        max_retries: int = 1,
    ) -> ExecutionOutcome:
        attempts = 0
        while True:
            attempts += 1
            try:
                if operation():
                    return ExecutionOutcome(success=True, attempts=attempts)
                failure = ExecutionFailure("UNKNOWN_ERROR", "Operation returned failure")
            except Exception as exc:
                code = error_code(exc) if error_code else "UNKNOWN_ERROR"
                failure = ExecutionFailure(code, str(exc))

            decision = self.policy.classify(failure.code, failure.message)
            if decision.action == ErrorAction.RETRY and attempts <= max_retries:
                continue

            return ExecutionOutcome(
                success=False,
                action=decision.action,
                error=failure,
                attempts=attempts,
            )
