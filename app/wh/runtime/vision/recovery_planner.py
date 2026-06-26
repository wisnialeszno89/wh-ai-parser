from app.wh.runtime.vision.recovery_plan import (
    RecoveryPlan
)


class RecoveryPlanner:

    def create(

        self,

        reason,

        brain

    ):

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