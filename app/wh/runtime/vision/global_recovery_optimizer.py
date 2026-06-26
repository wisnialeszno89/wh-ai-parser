from app.wh.runtime.vision.global_recovery_decision import (
    GlobalRecoveryDecision
)


class GlobalRecoveryOptimizer:

    def optimize(

        self,

        reason,

        brain

    ):

        local_best = (

            brain.best_recovery_strategy_finder.find(

                reason,

                brain

            )

        )

        if local_best is not None:

            return (

                GlobalRecoveryDecision(

                    strategy=local_best.strategy,

                    confidence=local_best.confidence

                )

            )

        global_best = (

            brain.global_best_strategy_finder.find(

                brain

            )

        )

        if global_best is not None:

            return (

                GlobalRecoveryDecision(

                    strategy=global_best.strategy,

                    confidence=global_best.confidence

                )

            )

        return None