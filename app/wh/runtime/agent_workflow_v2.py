from app.wh.runtime.action_planner_v2 import (
    ActionPlannerV2
)

from app.wh.runtime.gui_executor import (
    GUIExecutor
)


class AgentWorkflowV2:

    def __init__(

        self,

        mouse_enabled=False

    ):

        self.planner = (

            ActionPlannerV2()

        )

        self.executor = (

            GUIExecutor(

                mouse_enabled=mouse_enabled

            )

        )

    def execute(

        self,

        screenshot_path,

        templates_dir,

        construction

    ):

        plan = (

            self.planner.plan(

                construction

            )

        )

        return (

            self.executor.execute(

                screenshot_path,

                templates_dir,

                plan

            )

        )