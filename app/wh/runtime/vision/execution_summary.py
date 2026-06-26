from dataclasses import (
    dataclass
)


@dataclass
class ExecutionSummary:

    total_goals: int = 0

    success_count: int = 0

    failed_count: int = 0

    skipped_count: int = 0

    partial_success_count: int = 0

    human_review_count: int = 0