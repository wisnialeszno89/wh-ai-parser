from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.goal_risk_level import (
    GoalRiskLevel
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


@dataclass
class GoalAdaptiveModeDecision:

    goal_name: str

    risk_level: GoalRiskLevel

    mode: AdaptiveExecutionMode