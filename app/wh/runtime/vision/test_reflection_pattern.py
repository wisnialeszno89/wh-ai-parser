from app.wh.runtime.vision.reflection_pattern import (
    ReflectionPattern
)


def test_reflection_pattern():

    pattern = (

        ReflectionPattern(

            goal_name="enable_rc2",

            successes=5,

            failures=2

        )

    )

    assert (

        pattern.goal_name

        ==

        "enable_rc2"

    )

    assert (

        pattern.successes

        ==

        5

    )

    assert (

        pattern.failures

        ==

        2

    )