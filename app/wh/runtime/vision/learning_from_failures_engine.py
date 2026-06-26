from app.wh.runtime.vision.failure_learning_record import (
    FailureLearningRecord
)


class LearningFromFailuresEngine:

    def __init__(

        self

    ):

        self.records = []

    def learn(

        self,

        failure_reason,

        recovery_strategy,

        successful

    ):

        record = (

            FailureLearningRecord(

                failure_reason=(

                    failure_reason

                ),

                recovery_strategy=(

                    recovery_strategy

                ),

                successful=(

                    successful

                )

            )

        )

        self.records.append(

            record

        )

    def total_records(

        self

    ):

        return (

            len(

                self.records

            )

        )