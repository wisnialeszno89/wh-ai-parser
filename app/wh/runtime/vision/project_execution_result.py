from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.offer_execution_result import (
    OfferExecutionResult
)

from app.wh.runtime.vision.goal_execution_status import (
    GoalExecutionStatus
)


@dataclass
class ProjectExecutionResult:

    offer_result: OfferExecutionResult

    status: GoalExecutionStatus | None = None