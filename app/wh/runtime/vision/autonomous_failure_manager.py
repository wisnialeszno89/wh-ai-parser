from app.wh.runtime.vision.failure_pipeline import (
    FailurePipeline
)

from app.wh.runtime.vision.failure_record import (
    FailureRecord
)


class AutonomousFailureManager:

    def __init__(

        self

    ):

        self.pipeline = (

            FailurePipeline()

        )

    def handle(

        self,

        goal,

        reason,

        brain

    ):

        brain.failure_history.remember(

            FailureRecord(

                goal=goal.name,

                reason=reason

            )

        )

        return (

            self.pipeline.handle(

                reason,

                brain

            )

        )