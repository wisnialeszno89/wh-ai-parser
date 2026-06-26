from app.wh.runtime.vision.screenshot_provider import (
    ScreenshotProvider
)

from app.wh.runtime.vision.template_matcher import (
    TemplateMatcher
)

from app.wh.runtime.vision.mouse_controller import (
    MouseController
)

from app.wh.runtime.vision.keyboard_controller import (
    KeyboardController
)

from app.wh.runtime.vision.vision_action_registry import (
    VisionActionRegistry
)


class VisionRuntime:

    def __init__(

        self

    ):

        self.screenshot_provider = (

            ScreenshotProvider()

        )

        self.matcher = (

            TemplateMatcher()

        )

        self.mouse = (

            MouseController()

        )

        self.keyboard = (

            KeyboardController()

        )

        self.registry = (

            VisionActionRegistry(

                self

            )

        )

    def execute(

        self,

        action

    ):

        handler = (

            self.registry.resolve(

                action

            )

        )

        return handler.handle(

            action

        )