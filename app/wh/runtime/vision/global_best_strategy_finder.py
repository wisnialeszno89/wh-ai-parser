from app.wh.runtime.vision.global_best_strategy import (
    GlobalBestStrategy
)


class GlobalBestStrategyFinder:

    def find(

        self,

        brain

    ):

        best = None

        for record in (

            brain.meta_learning_memory.records

        ):

            if (

                best is None

                or

                record.successes

                >

                best.successes

            ):

                best = record

        if best is None:

            return None

        return (

            GlobalBestStrategy(

                strategy=best.strategy,

                confidence=best.successes

            )

        )