from app.wh.runtime.vision.goal_confidence import (
    GoalConfidence
)

from app.wh.runtime.vision.goal_confidence_level import (
    GoalConfidenceLevel
)

from app.wh.runtime.vision.goal_experience_level import (
    GoalExperienceLevel
)

from app.wh.runtime.vision.goal_risk_level import (
    GoalRiskLevel
)


class GoalConfidenceEngine:

    def evaluate(

        self,

        goal_risk,

        goal_experience

    ):

        if (

            goal_risk.risk_level

            ==

            GoalRiskLevel.LOW

            and

            goal_experience.level

            in (

                GoalExperienceLevel.HIGH,

                GoalExperienceLevel.VERY_HIGH

            )

        ):

            level = (

                GoalConfidenceLevel.VERY_HIGH

            )

        elif (

            goal_risk.risk_level

            ==

            GoalRiskLevel.HIGH

            and

            goal_experience.level

            ==

            GoalExperienceLevel.LOW

        ):

            level = (

                GoalConfidenceLevel.LOW

            )

        elif (

            goal_risk.risk_level

            ==

            GoalRiskLevel.MEDIUM

        ):

            level = (

                GoalConfidenceLevel.MEDIUM

            )

        else:

            level = (

                GoalConfidenceLevel.HIGH

            )

        return (

            GoalConfidence(

                goal_name=goal_risk.goal_name,

                level=level

            )

        )