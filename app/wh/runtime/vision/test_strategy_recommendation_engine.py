from app.wh.runtime.vision.strategy_recommendation_engine import (
    StrategyRecommendationEngine
)

from app.wh.runtime.vision.success_pattern_result import (
    SuccessPatternResult
)

from app.wh.runtime.vision.success_pattern import (
    SuccessPattern
)

from app.wh.runtime.vision.failure_pattern_result import (
    FailurePatternResult
)

from app.wh.runtime.vision.failure_pattern import (
    FailurePattern
)


def test_strategy_recommendation_engine():

    engine = (

        StrategyRecommendationEngine()

    )

    success_result = (

        SuccessPatternResult(

            patterns=[

                SuccessPattern(

                    pattern="Schuco+Antracyt+RC2",

                    successes=100

                )

            ]

        )

    )

    failure_result = (

        FailurePatternResult(

            patterns=[

                FailurePattern(

                    pattern="Softline82+RC3+HST",

                    failures=40

                )

            ]

        )

    )

    recommendation = (

        engine.recommend(

            success_result,

            failure_result

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