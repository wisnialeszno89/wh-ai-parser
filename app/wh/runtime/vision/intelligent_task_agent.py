from app.wh.runtime.vision.intelligent_vision_agent import (
    IntelligentVisionAgent
)

from app.wh.runtime.vision.task_execution_result import (
    TaskExecutionResult
)


class IntelligentTaskAgent:

    def __init__(

        self,

        runtime,

        brain

    ):

        self.agent = (

            IntelligentVisionAgent(

                runtime,

                brain

            )

        )

    def execute(

        self,

        task

    ):

        result = (

            TaskExecutionResult(

                task.name

            )

        )

        for goal in (

            task.goals

        ):

            goal_result = (

                self.agent.execute(

                    goal

                )

            )

            result.goal_results.append(

                goal_result

            )

        return result