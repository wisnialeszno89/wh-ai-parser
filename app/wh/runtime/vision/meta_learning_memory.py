from app.wh.runtime.vision.meta_learning_record import (
    MetaLearningRecord
)


class MetaLearningMemory:

    def __init__(

        self

    ):

        self.records = []

    def remember(

        self,

        strategy

    ):

        for record in (

            self.records

        ):

            if (

                record.strategy

                ==

                strategy

            ):

                record.successes += 1

                return

        self.records.append(

            MetaLearningRecord(

                strategy,

                successes=1

            )

        )

    def count(

        self

    ):

        return len(

            self.records

        )