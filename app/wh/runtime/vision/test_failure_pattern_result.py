from app.wh.runtime.vision.failure_pattern_result import (
    FailurePatternResult
)

from app.wh.runtime.vision.failure_pattern import (
    FailurePattern
)


def test_failure_pattern_result():

    result = (

        FailurePatternResult(

            patterns=[

                FailurePattern(

                    pattern="Softline82+RC3",

                    failures=10

                )

            ]

        )

    )

    assert (

        len(

            result.patterns

        )

        ==

        1

    )

    assert (

        result.patterns[0].failures

        ==

        10

    )