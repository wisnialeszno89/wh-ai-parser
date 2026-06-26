from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.goal_confidence_level import (
    GoalConfidenceLevel
)


@dataclass
class GoalConfidence:

    goal_name: str

    level: GoalConfidenceLevel