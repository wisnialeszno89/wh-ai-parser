from app.wh.runtime.vision.goal_risk import (
    GoalRisk
)

from app.wh.runtime.vision.goal_risk_level import (
    GoalRiskLevel
)


class GoalRiskEngine:

    def evaluate(

        self,

        pattern

    ):

        total = (

            pattern.successes

            +

            pattern.failures

        )

        if total == 0:

            rate = 0.0

        else:

            rate = (

                pattern.successes

                /

                total

            )

        if rate >= 0.8:

            level = (

                GoalRiskLevel.LOW

            )

        elif rate >= 0.5:

            level = (

                GoalRiskLevel.MEDIUM

            )

        else:

            level = (

                GoalRiskLevel.HIGH

            )

        return (

            GoalRisk(

                goal_name=pattern.goal_name,

                risk_level=level,

                success_rate=rate

            )

        )