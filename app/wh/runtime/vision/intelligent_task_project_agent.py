from app.wh.runtime.vision.intelligent_task_offer_agent import (
    IntelligentTaskOfferAgent
)

from app.wh.runtime.vision.project_execution_result import (
    ProjectExecutionResult
)


class IntelligentTaskProjectAgent:

    def __init__(

        self,

        runtime,

        brain

    ):

        self.offer_agent = (

            IntelligentTaskOfferAgent(

                runtime,

                brain

            )

        )

    def execute(

        self,

        project

    ):

        offer_result = (

            self.offer_agent.execute(

                project.offer

            )

        )

        return (

            ProjectExecutionResult(

                offer_result

            )

        )