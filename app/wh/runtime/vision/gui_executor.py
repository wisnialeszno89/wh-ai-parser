from app.wh.runtime.vision.tab_navigator import (
    TabNavigator
)


class GUIExecutor:

    def __init__(

        self,

        runtime

    ):

        self.runtime = runtime

        self.tab_navigator = (

            TabNavigator(

                runtime

            )

        )

    def execute(

        self,

        plan

    ):

        for step in (

            plan.steps

        ):

            if (

                step

                ==

                "goto_hardware"

            ):

                self.tab_navigator.goto(

                    "hardware"

                )

            elif (

                step

                ==

                "enable_rc2"

            ):

                pass

        return True