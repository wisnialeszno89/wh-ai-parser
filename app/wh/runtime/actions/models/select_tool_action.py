from dataclasses import dataclass

from app.wh.runtime.runtime_tool import (
    RuntimeTool
)

from app.wh.runtime.actions.models.runtime_action import (
    RuntimeAction
)


@dataclass
class SelectToolAction(RuntimeAction):

    tool: RuntimeTool

    def __init__(

        self,
        tool: RuntimeTool
    ):

        super().__init__(
            type="select_tool"
        )

        self.tool = tool