from app.gui.enums.gui_tool import (
    GuiTool,
)

from app.runtime.execution.debug.debug_overlay import (
    DebugOverlay,
)

from app.runtime.execution.models.screen_element import (
    ScreenElement,
)

from app.runtime.execution.vision.runtime_vision import (
    RuntimeVision,
)

from app.runtime.execution.vision.vision_adapter import (
    VisionAdapter,
)


class ToolLocator:

    def __init__(
        self,
        context,
    ):

        self.context = context

        self.vision = RuntimeVision()

        self.adapter = VisionAdapter()

        self.debug = DebugOverlay()

    def locate(
        self,
        tool: GuiTool,
    ) -> ScreenElement:

        print(
            f"[LOCATE] {tool.name}"
        )

        #
        # Cache screenshot
        #

        if self.context.cache.screenshot is None:

            screenshot = self.vision.capture()

            self.context.cache.screenshot = screenshot

        else:

            screenshot = self.context.cache.screenshot

            print(
                "[CACHE] Screenshot"
            )

        #
        # Cache objects
        #

        if self.context.cache.objects is None:

            objects = self.adapter.scene.analyze(

                screenshot,

                str(
                    self.adapter.templates
                ),

            )

            self.context.cache.objects = objects

        else:

            objects = self.context.cache.objects

            print(
                "[CACHE] Objects"
            )

        wanted = self.adapter.mapping.get(
            tool
        )

        if wanted is None:

            raise RuntimeError(

                f"No template mapped for {tool.name}"

            )

        for obj in objects:

            if obj.name != wanted:

                continue

            element = ScreenElement(

                name=tool.name,

                x=obj.x,

                y=obj.y,

                width=obj.width,

                height=obj.height,

                confidence=obj.confidence,

            )

            #
            # Save debug image.
            #

            self.debug.save(

                screenshot,

                element,

            )

            print(

                f"[VISION] FOUND "

                f"{element.name} "

                f"conf={element.confidence:.3f}"

            )

            return element

        raise RuntimeError(

            f"{tool.name} not found"

        )