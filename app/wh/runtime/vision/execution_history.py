from app.wh.runtime.vision.execution_record import (
    ExecutionRecord
)


class ExecutionHistory:

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