from app.wh.runtime.vision.failure_pattern import (
    FailurePattern
)


def test_failure_pattern():

    pattern = (

        FailurePattern(

            pattern="Softline82+RC3",

            failures=7

        )

    )

    assert (

        pattern.pattern

        ==

        "Softline82+RC3"

    )

    assert (

        pattern.failures

        ==

        7

    )