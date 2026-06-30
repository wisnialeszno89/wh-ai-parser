from app.runtime.models.runtime_plan import (
    RuntimePlan
)

from app.runtime.models.runtime_action import (
    RuntimeAction
)


class RuntimePlanner:

    def build(

        self,

        gui_plan,

        gui_knowledge

    ):

        plan = RuntimePlan()

        for action in gui_plan.actions:

            element = gui_knowledge.get(

                action.tool

            )

            if element is None:

                continue

            plan.actions.append(

                RuntimeAction(

                    action="CLICK",

                    payload=element

                )

            )

        return plan