from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Iterable


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
    ) -> QuoteReport:
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
            try:
                success = execute(item)
            except Exception as exc:  # isolate a single construction from the batch
                item.status = ItemStatus.FAILED
                item.issues.append(
                    PreflightIssue(
                        item_id=item.item_id,
                        severity=IssueSeverity.BLOCKING,
                        code="EXECUTION_EXCEPTION",
                        message=str(exc),
                    )
                )
                failed.append(item.item_id)
                issues.append(item.issues[-1])
                continue

            if success:
                item.status = ItemStatus.SUCCESS
                completed.append(item.item_id)
            else:
                item.status = ItemStatus.FAILED
                failed.append(item.item_id)

        return QuoteReport(
            completed=tuple(completed),
            skipped=tuple(skipped),
            failed=tuple(failed),
            issues=tuple(issues),
        )
