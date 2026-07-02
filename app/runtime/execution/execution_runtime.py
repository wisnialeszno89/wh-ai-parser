from app.gui.gui_plan import GuiPlan

from app.runtime.execution.action_executor import (
    ActionExecutor,
)

from app.runtime.execution.context.execution_context import (
    ExecutionContext,
)


class ExecutionRuntime:

    def __init__(

        self,

        context: ExecutionContext,

    ):

        self.context = context

        self.executor = ActionExecutor(
            context
        )

    def execute(
        self,
        gui_plan: GuiPlan,
    ):

        for action in gui_plan.actions:

            self.executor.execute(
                action
            )

        return True