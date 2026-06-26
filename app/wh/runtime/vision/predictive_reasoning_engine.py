from app.wh.runtime.vision.predictive_warning import (
    PredictiveWarning
)


class PredictiveReasoningEngine:

    def predict(

        self,

        goal,

        brain

    ):

        best = None

        for record in (

            brain.learning_memory.records

        ):

            if (

                record.value

                ==

                goal.name

            ):

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

            PredictiveWarning(

                reason=best.key,

                confidence=best.occurrences

            )

        )