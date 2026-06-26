from app.wh.runtime.vision.failure_executor import (
    FailureExecutor
)

from app.wh.runtime.vision.failure_reasoning_engine import (
    FailureReasoningEngine
)


class FailurePipeline:

    def __init__(

        self

    ):

        self.reasoning_engine = (

            FailureReasoningEngine()

        )

        self.executor = (

            FailureExecutor()

        )

    def handle(

        self,

        reason,

        brain

    ):

        decision = (

            self.reasoning_engine.decide(

                reason,

                brain

            )

        )

        return (

            self.executor.execute(

                decision,

                brain

            )

        )