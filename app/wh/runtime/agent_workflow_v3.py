from app.wh.runtime.construction_planner import (
    ConstructionPlanner
)

from app.wh.runtime.gui_executor import (
    GUIExecutor
)


class AgentWorkflowV3:

    def __init__(

        self,

        mouse_enabled=False

    ):

        self.planner = (

            ConstructionPlanner()

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