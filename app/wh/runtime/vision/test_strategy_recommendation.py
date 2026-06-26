from app.wh.runtime.vision.strategy_recommendation import (
    StrategyRecommendation
)


def test_strategy_recommendation():

    recommendation = (

        StrategyRecommendation(

            preferred_patterns=[

                "Schuco+Antracyt+RC2"

            ],

            risky_patterns=[

                "Softline82+RC3+HST"

            ]

        )

    )

    assert (

        recommendation.preferred_patterns[0]

        ==

        "Schuco+Antracyt+RC2"

    )

    assert (

        recommendation.risky_patterns[0]

        ==

        "Softline82+RC3+HST"

    )