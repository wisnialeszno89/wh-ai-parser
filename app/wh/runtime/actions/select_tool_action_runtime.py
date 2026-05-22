from app.wh.runtime.actions.base_action import (
    BaseAction
)

from app.wh.runtime.runtime_tool import (
    RuntimeTool
)


class SelectToolActionRuntime(

    BaseAction
):

    def __init__(

        self,
        tool
    ):

        self.tool = tool

    def execute(

        self,
        runtime
    ):

        runtime.select_tool(

            RuntimeTool(
                self.tool
            )
        )

    def serialize(self):

        return {

            "type": "select_tool",

            "tool": self.tool
        }