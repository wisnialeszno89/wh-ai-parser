from app.wh.runtime.vision.goal_risk_engine import (
    GoalRiskEngine
)

from app.wh.runtime.vision.reflection_pattern import (
    ReflectionPattern
)

from app.wh.runtime.vision.goal_risk_level import (
    GoalRiskLevel
)


def test_goal_risk_engine():

    engine = (

        GoalRiskEngine()

    )

    pattern = (

        ReflectionPattern(

            goal_name="enable_rc2",

            successes=8,

            failures=2

        )

    )

    risk = (

        engine.evaluate(

            pattern

        )

    )

    assert (

        risk.goal_name

        ==

        "enable_rc2"

    )

    assert (

        risk.risk_level

        ==

        GoalRiskLevel.LOW

    )

    assert (

        risk.success_rate

        ==

        0.8

    )