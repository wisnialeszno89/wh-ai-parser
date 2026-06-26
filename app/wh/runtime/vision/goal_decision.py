from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.goal_confidence_level import (
    GoalConfidenceLevel
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


@dataclass
class GoalDecision:

    goal_name: str

    confidence_level: GoalConfidenceLevel

    execution_mode: AdaptiveExecutionMode