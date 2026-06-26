from app.wh.runtime.vision.goal_experience_engine import (
    GoalExperienceEngine
)

from app.wh.runtime.vision.reflection_pattern import (
    ReflectionPattern
)

from app.wh.runtime.vision.goal_experience_level import (
    GoalExperienceLevel
)


def test_goal_experience_engine():

    engine = (

        GoalExperienceEngine()

    )

    pattern = (

        ReflectionPattern(

            goal_name="enable_rc2",

            successes=20,

            failures=10

        )

    )

    result = (

        engine.evaluate(

            pattern

        )

    )

    assert (

        result.goal_name

        ==

        "enable_rc2"

    )

    assert (

        result.level

        ==

        GoalExperienceLevel.HIGH

    )

    assert (

        result.total_executions

        ==

        30

    )