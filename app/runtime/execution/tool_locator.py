from app.gui.enums.gui_tool import GuiTool

from app.runtime.execution.models.screen_element import (
    ScreenElement,
)


class ToolLocator:

    def __init__(
        self,
        context,
    ):
        self.context = context

    def locate(
        self,
        tool: GuiTool,
    ) -> ScreenElement:

        print(
            f"[LOCATE] {tool.name}"
        )

        #
        # Temporary fake element.
        # Następny sprint zastąpi to Vision.
        #

        return ScreenElement(
            name=tool.name,
            x=0,
            y=0,
            width=32,
            height=32,
            confidence=1.0,
        )