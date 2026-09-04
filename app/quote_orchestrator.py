from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable

from app.wh.runtime.controlled_executor import ControlledExecutor
from app.wh.runtime.error_policy import ErrorAction


class IssueSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    DECISION_REQUIRED = "decision_required"
    BLOCKING = "blocking"
    FATAL = "fatal"


class ItemStatus(str, Enum):
    READY = "ready"
    SKIPPED = "skipped"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"


@dataclass(frozen=True)
class PreflightIssue:
    item_id: str
    severity: IssueSeverity
    code: str
    message: str


@dataclass
class QuoteItem:
    item_id: str
    payload: Any
    status: ItemStatus = ItemStatus.READY
    issues: list[PreflightIssue] = field(default_factory=list)


@dataclass(frozen=True)
class QuoteReport:
    completed: tuple[str, ...]
    skipped: tuple[str, ...]
    failed: tuple[str, ...]
    issues: tuple[PreflightIssue, ...]

    @property
    def total(self) -> int:
        return len(set(self.completed) | set(self.skipped) | set(self.failed))


class QuoteOrchestrator:
    """Runs a quote item-by-item without letting one bad item stop the batch."""

    def preflight(
        self,
        items: Iterable[QuoteItem],
        validator: Callable[[QuoteItem], Iterable[PreflightIssue]],
    ) -> list[QuoteItem]:
        prepared = list(items)
        for item in prepared:
            item.issues = list(validator(item))
            if any(issue.severity in {IssueSeverity.BLOCKING, IssueSeverity.FATAL} for issue in item.issues):
                item.status = ItemStatus.SKIPPED
        return prepared

    def run(
        self,
        items: Iterable[QuoteItem],
        execute: Callable[[QuoteItem], bool],
        controlled_executor: ControlledExecutor | None = None,
        error_code: Callable[[Exception], str] | None = None,
        max_retries: int = 1,
    ) -> QuoteReport:
        """Execute quote items resiliently and preserve actionable WH failures."""
        executor = controlled_executor or ControlledExecutor()
        completed: list[str] = []
        skipped: list[str] = []
        failed: list[str] = []
        issues: list[PreflightIssue] = []

        for item in items:
            issues.extend(item.issues)
            if item.status == ItemStatus.SKIPPED:
                skipped.append(item.item_id)
                continue

            item.status = ItemStatus.EXECUTING
            effective_error_code = error_code or (lambda _: "EXECUTION_EXCEPTION")
            outcome = executor.run(
                lambda item=item: execute(item),
                error_code=effective_error_code,
                max_retries=max_retries,
            )

            if outcome.success:
                item.status = ItemStatus.SUCCESS
                completed.append(item.item_id)
                continue

            failure = outcome.error
            code = failure.code if failure else "UNKNOWN_ERROR"
            message = failure.message if failure else "Execution failed"
            severity = (
                IssueSeverity.DECISION_REQUIRED
                if outcome.action in {ErrorAction.SKIP, ErrorAction.ACKNOWLEDGE}
                else IssueSeverity.BLOCKING
            )
            item.issues.append(
                PreflightIssue(
                    item_id=item.item_id,
                    severity=severity,
                    code=code,
                    message=message,
                )
            )
            issues.append(item.issues[-1])

            if outcome.action in {ErrorAction.SKIP, ErrorAction.ACKNOWLEDGE}:
                item.status = ItemStatus.SKIPPED
                skipped.append(item.item_id)
            else:
                item.status = ItemStatus.FAILED
                failed.append(item.item_id)

        return QuoteReport(
            completed=tuple(completed),
            skipped=tuple(skipped),
            failed=tuple(failed),
            issues=tuple(issues),
        )
