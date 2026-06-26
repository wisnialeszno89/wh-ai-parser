from app.wh.runtime.vision.strategy_recommendation import (
    StrategyRecommendation
)


class StrategyRecommendationEngine:

    def recommend(

        self,

        success_patterns,

        failure_patterns

    ):

        preferred = []

        risky = []

        for pattern in (

            success_patterns.patterns[:5]

        ):

            preferred.append(

                pattern.pattern

            )

        for pattern in (

            failure_patterns.patterns[:5]

        ):

            risky.append(

                pattern.pattern

            )

        return (

            StrategyRecommendation(

                preferred_patterns=preferred,

                risky_patterns=risky

            )

        )