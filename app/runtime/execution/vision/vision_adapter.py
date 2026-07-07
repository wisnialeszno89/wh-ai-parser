from pathlib import Path

from app.gui.enums.gui_tool import GuiTool

from app.runtime.execution.models.screen_element import (
    ScreenElement,
)

from app.wh.vision.screen_scene_graph import (
    ScreenSceneGraph,
)

from app.wh.vision.screenshot import (
    Screenshot,
)


class VisionAdapter:

    def __init__(self):

        self.scene = ScreenSceneGraph()

        self.templates = Path("templates")

        self.mapping = {

            GuiTool.FRAME: "frame_tool.png",

            GuiTool.SASH: "sash_tool.png",

            GuiTool.GLASS: "glass_tool.png",

            GuiTool.HARDWARE: "hardware_tool.png",
            
	    GuiTool.SAVE: "close_button.png",

        }

    def locate(

        self,

        screenshot: Screenshot,

        tool: GuiTool,

    ) -> ScreenElement:

        objects = self.scene.analyze(

            screenshot,

            str(self.templates),

        )

        wanted = self.mapping.get(tool)

        if wanted is None:

            raise RuntimeError(

                f"No template mapped for {tool.name}"

            )

        for obj in objects:

            if obj.name != wanted:

                continue

            return ScreenElement(

                name=tool.name,

                x=obj.x,

                y=obj.y,

                width=obj.width,

                height=obj.height,

                confidence=obj.confidence,

            )

        raise RuntimeError(

            f"{tool.name} not found"

        )