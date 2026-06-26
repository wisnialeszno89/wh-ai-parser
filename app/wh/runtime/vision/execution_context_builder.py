from app.wh.runtime.vision.pre_execution_advisor import (
    PreExecutionAdvisor
)

from app.wh.runtime.vision.execution_context_factory import (
    ExecutionContextFactory
)


class ExecutionContextBuilder:

    def __init__(

        self

    ):

        self.advisor = (

            PreExecutionAdvisor()

        )

        self.factory = (

            ExecutionContextFactory()

        )

    def build(

        self,

        goal,

        brain

    ):

        advice = (

            self.advisor.advise(

                goal,

                brain

            )

        )

        mode = (

            brain.adaptive_execution_mode_engine.decide(

                advice.strategy

            )

        )

        return (

            self.factory.create(

                mode

            )

        )