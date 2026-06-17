from app.wh.runtime.action_planner import (
    ActionPlanner
)

from app.wh.runtime.runtime_engine import (
    RuntimeEngine
)


class AutomationEngine:

    def __init__(

        self

    ):

        self.planner = (

            ActionPlanner()

        )

        self.runtime = (

            RuntimeEngine()

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

        return (

            self.runtime.execute(

                actions

            )

        )