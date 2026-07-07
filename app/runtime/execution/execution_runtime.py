from app.gui.gui_plan import (
    GuiPlan,
)

from app.runtime.execution.context.execution_context import (
    ExecutionContext,
)

from app.runtime.mission.mission import (
    Mission,
)

from app.runtime.mission.mission_executor import (
    MissionExecutor,
)


class ExecutionRuntime:

    def __init__(

        self,

        context: ExecutionContext,

    ):

        self.executor = MissionExecutor(
            context
        )

    def execute(

        self,

        gui_plan: GuiPlan,

    ):

        mission = Mission(

            name="Build window",

            gui_plan=gui_plan,

        )

        state = self.executor.execute(

            mission

        )

        return state.completed