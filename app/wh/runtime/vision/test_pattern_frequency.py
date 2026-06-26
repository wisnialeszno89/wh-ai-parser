from app.wh.runtime.vision.pattern_frequency import (
    PatternFrequency
)


def test_pattern_frequency():

    result = (

        PatternFrequency(

            pattern="Softline82+RC2",

            count=15

        )

    )

    assert (

        result.pattern

        ==

        "Softline82+RC2"

    )

    assert (

        result.count

        ==

        15

    )