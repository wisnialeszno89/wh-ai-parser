from pathlib import Path

from app.runtime.execution.models.screen_element import (
    ScreenElement,
)

from app.wh.vision.screen_scene_graph import (
    ScreenSceneGraph,
)


class VisionAdapter:

    def __init__(self):

        self.scene_graph = ScreenSceneGraph()

    def locate(

        self,

        screenshot,

        templates_dir,

        tool_name,

    ) -> ScreenElement:

        objects = self.scene_graph.analyze(

            screenshot,

            templates_dir,

        )

        #
        # Szukamy tylko właściwego narzędzia.
        #

        for obj in objects:

            template_name = Path(obj.name).stem.upper()

            if template_name != tool_name.upper():

                continue

            return ScreenElement(

                name=tool_name,

                x=obj.x,

                y=obj.y,

                width=obj.width,

                height=obj.height,

                confidence=obj.confidence,

            )

        raise RuntimeError(

            f"{tool_name} not found"

        )