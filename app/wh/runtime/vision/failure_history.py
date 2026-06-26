from app.wh.runtime.vision.failure_record import (
    FailureRecord
)


class FailureHistory:

    def __init__(

        self

    ):

        self.records = []

    def remember(

        self,

        record

    ):

        self.records.append(

            record

        )

    def count(

        self

    ):

        return len(

            self.records

        )