from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.goal_execution_status import (
    GoalExecutionStatus
)


@dataclass
class GoalExecutionResult:

    status: GoalExecutionStatus

    reason: str | None = None