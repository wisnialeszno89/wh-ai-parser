from app.gui.enums.gui_tool import (
    GuiTool,
)

from app.runtime.execution.models.screen_element import (
    ScreenElement,
)

from app.runtime.execution.vision.runtime_vision import (
    RuntimeVision,
)


class ToolLocator:

    def __init__(
        self,
        context,
    ):

        self.context = context

        self.vision = RuntimeVision()

    def locate(
        self,
        tool: GuiTool,
    ) -> ScreenElement:

        print(
            f"[LOCATE] {tool.name}"
        )

        #
        # Pierwszy prawdziwy krok Vision.
        #

        image = self.vision.capture()

        print(
            f"[VISION] Image shape: {image.shape}"
        )

        #
        # Następny sprint:
        #
        # ToolbarDetector
        # CandidateExtractor
        #

        return ScreenElement(
            name=tool.name,
            x=0,
            y=0,
            width=32,
            height=32,
            confidence=1.0,
        )