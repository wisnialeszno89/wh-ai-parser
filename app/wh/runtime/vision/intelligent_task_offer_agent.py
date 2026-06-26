from app.wh.runtime.vision.vision_task_compiler import (
    VisionTaskCompiler
)

from app.wh.runtime.vision.intelligent_task_agent import (
    IntelligentTaskAgent
)

from app.wh.runtime.vision.offer_execution_result import (
    OfferExecutionResult
)


class IntelligentTaskOfferAgent:

    def __init__(

        self,

        runtime,

        brain

    ):

        self.compiler = (

            VisionTaskCompiler()

        )

        self.agent = (

            IntelligentTaskAgent(

                runtime,

                brain

            )

        )

    def execute(

        self,

        offer

    ):

        result = (

            OfferExecutionResult()

        )

        tasks = (

            self.compiler.compile(

                offer

            )

        )

        for task in (

            tasks

        ):

            task_result = (

                self.agent.execute(

                    task

                )

            )

            result.task_results.append(

                task_result

            )

        return result