from app.wh.runtime.vision.adaptive_recovery_result import (
    AdaptiveRecoveryResult
)


class AdaptiveRecoveryEngine:

    def recover(

        self,

        brain,

        failure_reason

    ):

        recommendation = (

            brain.recovery_strategy_selector.recommend(

                brain.recovery_knowledge_base,

                failure_reason

            )

        )

        strategy = (

            recommendation.recovery_strategy

        )

        success = True

        brain.recovery_knowledge_base.remember(

            failure_reason,

            strategy,

            success

        )

        return (

            AdaptiveRecoveryResult(

                success=success,

                strategy_used=strategy,

                confidence=(

                    recommendation.confidence

                )

            )

        )