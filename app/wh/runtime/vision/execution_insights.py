from dataclasses import (
    dataclass
)


@dataclass
class ExecutionInsights:

    success_rate: float = 100.0

    most_common_failure_reason: str | None = None

    human_review_count: int = 0

    failed_goal_count: int = 0