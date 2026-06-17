from app.wh.runtime.engines.base_engine import (
    BaseEngine
)

from app.wh.runtime.actions.action import (
    Action
)

from app.wh.runtime.actions.action_plan import (
    ActionPlan
)


class PSKEngine(

    BaseEngine

):

    def execute(

        self,

        construction

    ):

        plan = (

            ActionPlan()

        )

        plan.add(

            Action(

                "frame",

                "frame_button.png"

            )

        )

        return plan