from app.wh.runtime.vision.goal_experience import (
    GoalExperience
)

from app.wh.runtime.vision.goal_experience_level import (
    GoalExperienceLevel
)


class GoalExperienceEngine:

    def evaluate(

        self,

        pattern

    ):

        total = (

            pattern.successes

            +

            pattern.failures

        )

        if total >= 100:

            level = (

                GoalExperienceLevel.VERY_HIGH

            )

        elif total >= 25:

            level = (

                GoalExperienceLevel.HIGH

            )

        elif total >= 5:

            level = (

                GoalExperienceLevel.MEDIUM

            )

        else:

            level = (

                GoalExperienceLevel.LOW

            )

        return (

            GoalExperience(

                goal_name=pattern.goal_name,

                level=level,

                total_executions=total

            )

        )