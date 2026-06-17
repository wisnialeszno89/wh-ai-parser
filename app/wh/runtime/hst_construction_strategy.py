from app.wh.runtime.action_planner_v2 import (
    ActionPlannerV2
)

from app.wh.runtime.construction_strategy import (
    ConstructionStrategy
)


class HSTConstructionStrategy(

    ConstructionStrategy

):

    def __init__(

        self

    ):

        self.planner = (

            ActionPlannerV2()

        )

    def plan(

        self,

        construction

    ):

        return (

            self.planner.plan(

                construction

            )

        )