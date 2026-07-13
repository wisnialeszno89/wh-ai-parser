from app.runtime.execution.vision.runtime_vision import (
    RuntimeVision,
)

from app.runtime.execution.vision.vision_adapter import (
    VisionAdapter,
)

from app.runtime.world.world_state import (
    WorldState,
)


class PerceptionEngine:

    def __init__(
        self,
    ):

        self.vision = RuntimeVision()

        self.adapter = VisionAdapter()

    def perceive(
        self,
    ) -> WorldState:

        vision = self.vision.capture()

        objects = self.adapter.scene.analyze(

            vision.screenshot,

            str(
                self.adapter.templates
            ),

        )

        world = WorldState()

        world.screenshot = vision.screenshot

        world.objects = objects

        #
        # Pierwsza interpretacja świata.
        #

        world.toolbar_visible = len(objects) > 0

        for obj in objects:

            if "frame_tool" in obj.name:

                world.active_tool = "FRAME"

                break

        return world