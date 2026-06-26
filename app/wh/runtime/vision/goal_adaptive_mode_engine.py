from app.wh.runtime.vision.goal_adaptive_mode_decision import (
    GoalAdaptiveModeDecision
)

from app.wh.runtime.vision.goal_risk_level import (
    GoalRiskLevel
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


class GoalAdaptiveModeEngine:

    def decide(

        self,

        goal_risk

    ):

        if (

            goal_risk.risk_level

            ==

            GoalRiskLevel.LOW

        ):

            mode = (

                AdaptiveExecutionMode.NORMAL

            )

        elif (

            goal_risk.risk_level

            ==

            GoalRiskLevel.MEDIUM

        ):

            mode = (

                AdaptiveExecutionMode.CAREFUL_MODE

            )

        else:

            mode = (

                AdaptiveExecutionMode.SAFE_MODE

            )

        return (

            GoalAdaptiveModeDecision(

                goal_name=goal_risk.goal_name,

                risk_level=goal_risk.risk_level,

                mode=mode

            )

        )