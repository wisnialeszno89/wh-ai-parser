from app.wh.runtime.vision.learning_record import (
    LearningRecord
)


class LearningMemory:

    def __init__(

        self

    ):

        self.records = []

    def remember(

        self,

        key,

        value

    ):

        for record in (

            self.records

        ):

            if (

                record.key == key

                and

                record.value == value

            ):

                record.occurrences += 1

                return

        self.records.append(

            LearningRecord(

                key,

                value

            )

        )

    def count(

        self

    ):

        return len(

            self.records

        )