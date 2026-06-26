from app.wh.runtime.vision.best_recovery_strategy import (
    BestRecoveryStrategy
)


class BestRecoveryStrategyFinder:

    def find(

        self,

        reason,

        brain

    ):

        best = None

        for record in (

            brain.recovery_learning_memory.records

        ):

            if (

                record.reason

                !=

                reason

            ):

                continue

            if (

                best is None

                or

                record.occurrences

                >

                best.occurrences

            ):

                best = record

        if best is None:

            return None

        return (

            BestRecoveryStrategy(

                strategy=best.strategy,

                confidence=best.occurrences

            )

        )