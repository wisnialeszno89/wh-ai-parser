from app.wh.runtime.vision.recovery_strategy_recommendation import (
    RecoveryStrategyRecommendation
)


class RecoveryStrategySelector:

    def recommend(

        self,

        knowledge_base,

        failure_reason

    ):

        best = None

        best_score = -1

        for item in (

            knowledge_base.knowledge.values()

        ):

            if (

                item.failure_reason

                !=

                failure_reason

            ):

                continue

            score = (

                item.success_count

            )

            if score > best_score:

                best = item

                best_score = score

        if best is None:

            return (

                RecoveryStrategyRecommendation(

                    failure_reason=failure_reason,

                    recovery_strategy="FULL_RETRY",

                    confidence=0.0

                )

            )

        total = (

            best.success_count

            +

            best.failure_count

        )

        confidence = 0.0

        if total > 0:

            confidence = (

                best.success_count

                /

                total

            )

        return (

            RecoveryStrategyRecommendation(

                failure_reason=best.failure_reason,

                recovery_strategy=best.recovery_strategy,

                confidence=confidence

            )

        )