from app.wh.runtime.vision.goal_decision import (
    GoalDecision
)

from app.wh.runtime.vision.goal_risk import (
    GoalRisk
)

from app.wh.runtime.vision.goal_risk_level import (
    GoalRiskLevel
)

from app.wh.runtime.vision.goal_experience import (
    GoalExperience
)

from app.wh.runtime.vision.goal_experience_level import (
    GoalExperienceLevel
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


class GoalDecisionEngine:

    def decide(

        self,

        goal_confidence

    ):

        if (

            goal_confidence.level.value

            ==

            "very_high"

        ):

            mode = (

                AdaptiveExecutionMode.NORMAL

            )

        elif (

            goal_confidence.level.value

            ==

            "high"

        ):

            mode = (

                AdaptiveExecutionMode.CAREFUL_MODE

            )

        elif (

            goal_confidence.level.value

            ==

            "medium"

        ):

            mode = (

                AdaptiveExecutionMode.SAFE_MODE

            )

        else:

            mode = (

                AdaptiveExecutionMode.HUMAN_REVIEW_MODE

            )

        return (

            GoalDecision(

                goal_name=goal_confidence.goal_name,

                confidence_level=goal_confidence.level,

                execution_mode=mode

            )

        )