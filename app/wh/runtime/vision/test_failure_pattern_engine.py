from app.wh.runtime.vision.failure_pattern_engine import (
    FailurePatternEngine
)


def test_failure_pattern_engine():

    engine = (

        FailurePatternEngine()

    )

    result = (

        engine.analyze(

            [

                "Softline82+RC3",

                "Softline82+RC3",

                "Schuco+Antracyt",

                "Softline82+RC3",

                "Schuco+Antracyt"

            ]

        )

    )

    assert (

        len(

            result.patterns

        )

        ==

        2

    )

    assert (

        result.patterns[0].pattern

        ==

        "Softline82+RC3"

    )

    assert (

        result.patterns[0].failures

        ==

        3

    )