from app.wh.runtime.vision.gui_plan import (
    GUIPlan
)


class GUIPlanner:

    def create_plan(

        self,

        goal

    ):

        plan = (

            GUIPlan()

        )

        if (

            goal.name

            ==

            "enable_rc2"

        ):

            plan.add(

                "goto_hardware"

            )

            plan.add(

                "enable_rc2"

            )

        return plan