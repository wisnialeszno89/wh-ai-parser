from app.wh.runtime.vision.success_pattern_result import (
    SuccessPatternResult
)

from app.wh.runtime.vision.success_pattern import (
    SuccessPattern
)


def test_success_pattern_result():

    result = (

        SuccessPatternResult(

            patterns=[

                SuccessPattern(

                    pattern="Schuco+Antracyt",

                    successes=20

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

        result.patterns[0].successes

        ==

        20

    )