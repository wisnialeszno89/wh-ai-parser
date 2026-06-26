from dataclasses import (
    dataclass
)

from app.wh.runtime.vision.goal_experience_level import (
    GoalExperienceLevel
)


@dataclass
class GoalExperience:

    goal_name: str

    level: GoalExperienceLevel

    total_executions: int