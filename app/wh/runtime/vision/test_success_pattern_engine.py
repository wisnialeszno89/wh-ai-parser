from app.wh.runtime.vision.success_pattern_engine import (
    SuccessPatternEngine
)


def test_success_pattern_engine():

    engine = (

        SuccessPatternEngine()

    )

    result = (

        engine.analyze(

            [

                "Schuco+Antracyt",

                "Schuco+Antracyt",

                "Softline82+RC2",

                "Schuco+Antracyt",

                "Softline82+RC2"

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

        "Schuco+Antracyt"

    )

    assert (

        result.patterns[0].successes

        ==

        3

    )