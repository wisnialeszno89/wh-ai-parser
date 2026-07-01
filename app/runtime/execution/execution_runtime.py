from app.gui.gui_plan import GuiPlan

from app.runtime.execution.action_executor import (
    ActionExecutor,
)


class ExecutionRuntime:

    def __init__(self):
        self.executor = ActionExecutor()

    def execute(
        self,
        gui_plan: GuiPlan,
    ):

        for action in gui_plan.actions:
            self.executor.execute(action)

        return True