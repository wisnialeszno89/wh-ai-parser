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

    def run_batch(
        self,
        operations: list[tuple[str, Callable[[], bool]]],
        error_code: Callable[[Exception], str] | None = None,
        max_retries: int = 1,
    ) -> tuple[dict[str, ExecutionOutcome], bool]:
        """Execute all independent operations and report whether the batch may continue.

        A SKIP/ACKNOWLEDGE result never stops the batch. RETRY is handled inside
        ``run``. STOP is the only result that requests a global stop.
        """
        outcomes: dict[str, ExecutionOutcome] = {}
        should_stop = False

        for operation_id, operation in operations:
            outcome = self.run(
                operation,
                error_code=error_code,
                max_retries=max_retries,
            )
            outcomes[operation_id] = outcome
            if outcome.action == ErrorAction.STOP:
                should_stop = True

        return outcomes, should_stop
