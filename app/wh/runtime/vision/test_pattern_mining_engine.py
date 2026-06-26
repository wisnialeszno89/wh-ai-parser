from app.wh.runtime.vision.pattern_mining_engine import (
    PatternMiningEngine
)


def test_pattern_mining_engine():

    engine = (

        PatternMiningEngine()

    )

    result = (

        engine.analyze(

            [

                "Softline82+RC2",

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

        "Softline82+RC2"

    )

    assert (

        result.patterns[0].count

        ==

        3

    )