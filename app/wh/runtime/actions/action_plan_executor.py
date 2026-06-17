from app.wh.runtime.action_executor import (
    ActionExecutor
)


class ActionPlanExecutor:

    def __init__(

        self

    ):

        self.executor = (

            ActionExecutor()

        )

    def execute(

        self,

        plan

    ):

        for action in plan.actions:

            self.executor.execute_action(

                action

            )

        return True