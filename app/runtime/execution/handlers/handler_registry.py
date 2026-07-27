from app.gui.enums.gui_tool import (
    GuiTool,
)

from app.runtime.execution.handlers.frame_handler import (
    FrameHandler,
)


class HandlerRegistry:

    def __init__(self):

        self.handlers = {

            GuiTool.FRAME: FrameHandler(),

        }

    def get(
        self,
        tool,
    ):

        return self.handlers.get(
            tool,
        )