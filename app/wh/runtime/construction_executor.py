from app.wh.runtime.construction_action_planner import (
    ConstructionActionPlanner
)

from app.wh.runtime.action_executor import (
    ActionExecutor
)


class ConstructionExecutor:

    def __init__(

        self

    ):

        self.planner = (

            ConstructionActionPlanner()

        )

        self.executor = (

            ActionExecutor()

        )

    def execute(

        self,

        construction

    ):

        actions = (

            self.planner.plan(

                construction

            )

        )

        for action in actions:

            self.executor.execute_action(

                action

            )

        return True