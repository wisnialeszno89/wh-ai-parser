from app.wh.runtime.vision.recovery_plan import (
    RecoveryPlan
)


class IntelligentRecoveryPlanner:

    def create(

        self,

        reason,

        brain

    ):

        best = (

            brain.best_recovery_strategy_finder.find(

                reason,

                brain

            )

        )

        if best is not None:

            return (

                RecoveryPlan(

                    strategy=best.strategy,

                    reason=reason

                )

            )

        strategy = (

            brain.alternative_strategy_engine.choose(

                reason

            )

        )

        return (

            RecoveryPlan(

                strategy=strategy,

                reason=reason

            )

        )