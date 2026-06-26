from app.wh.runtime.vision.pattern_mining_result import (
    PatternMiningResult
)

from app.wh.runtime.vision.pattern_frequency import (
    PatternFrequency
)


def test_pattern_mining_result():

    result = (

        PatternMiningResult(

            patterns=[

                PatternFrequency(

                    pattern="Softline82+RC2",

                    count=20

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

        result.patterns[0].count

        ==

        20

    )