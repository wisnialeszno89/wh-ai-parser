from app.gui.enums.gui_tool import GuiTool

from app.runtime.execution.models.screen_element import (
    ScreenElement,
)


class VisionEngine:

    def locate_tool(
        self,
        screenshot,
        tool: GuiTool,
    ) -> ScreenElement:

        raise NotImplementedError()