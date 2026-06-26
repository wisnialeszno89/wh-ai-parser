from app.wh.runtime.vision.recovery_learning_record import (
    RecoveryLearningRecord
)


class RecoveryLearningMemory:

    def __init__(

        self

    ):

        self.records = []

    def remember(

        self,

        reason,

        strategy

    ):

        for record in (

            self.records

        ):

            if (

                record.reason == reason

                and

                record.strategy == strategy

            ):

                record.occurrences += 1

                return

        self.records.append(

            RecoveryLearningRecord(

                reason,

                strategy

            )

        )

    def count(

        self

    ):

        return len(

            self.records

        )