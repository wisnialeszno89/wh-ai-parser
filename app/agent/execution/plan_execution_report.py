from dataclasses import dataclass

from app.agent.execution.execution_result import (
    ExecutionResult,
)


@dataclass(frozen=True)
class PlanExecutionReport:
    """
    Aggregated execution report for a complete action plan.
    """

    results: tuple[ExecutionResult, ...]

    @property
    def success(self) -> bool:
        return all(
            result.success
            for result in self.results
        )

    @property
    def requires_manual_review(self) -> bool:
        return any(
            result.requires_manual_review
            for result in self.results
        )
