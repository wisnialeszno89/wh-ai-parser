from app.wh.runtime.vision.execution_record import (
    ExecutionRecord
)


class ExecutionLogger:

    def log(

        self,

        goal,

        decision,

        success,

        brain

    ):

        record = (

            ExecutionRecord(

                goal=goal.name,

                success=success,

                reason=decision.reason

            )

        )

        brain.execution_history.remember(

            record

        )