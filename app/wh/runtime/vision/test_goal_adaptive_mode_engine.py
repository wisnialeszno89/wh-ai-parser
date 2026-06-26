from app.wh.runtime.vision.goal_adaptive_mode_engine import (
    GoalAdaptiveModeEngine
)

from app.wh.runtime.vision.goal_risk import (
    GoalRisk
)

from app.wh.runtime.vision.goal_risk_level import (
    GoalRiskLevel
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


def test_goal_adaptive_mode_engine():

    engine = (

        GoalAdaptiveModeEngine()

    )

    low = (

        GoalRisk(

            goal_name="enable_rc2",

            risk_level=(

                GoalRiskLevel.LOW

            ),

            success_rate=0.9

        )

    )

    medium = (

        GoalRisk(

            goal_name="enable_contacts",

            risk_level=(

                GoalRiskLevel.MEDIUM

            ),

            success_rate=0.6

        )

    )

    high = (

        GoalRisk(

            goal_name="enable_alarm",

            risk_level=(

                GoalRiskLevel.HIGH

            ),

            success_rate=0.2

        )

    )

    assert (

        engine.decide(

            low

        ).mode

        ==

        AdaptiveExecutionMode.NORMAL

    )

    assert (

        engine.decide(

            medium

        ).mode

        ==

        AdaptiveExecutionMode.CAREFUL_MODE

    )

    assert (

        engine.decide(

            high

        ).mode

        ==

        AdaptiveExecutionMode.SAFE_MODE

    )