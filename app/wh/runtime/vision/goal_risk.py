from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.goal_risk_level import (
    GoalRiskLevel
)


@dataclass
class GoalRisk:

    goal_name: str

    risk_level: GoalRiskLevel

    success_rate: float