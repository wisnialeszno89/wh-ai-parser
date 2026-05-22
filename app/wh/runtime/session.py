from app.wh.runtime.geometry.factory import (
    GeometryFactory
)

from app.wh.runtime.canvas.detector import (
    CanvasDetector
)

from app.wh.runtime.actions.waiters import (
    RuntimeWaiters
)

from app.wh.runtime.screenshots.screenshot_store import (
    ScreenshotStore
)

from app.wh.runtime.hooks.runtime_hooks import (
    RuntimeHooks
)

from app.wh.runtime.drivers.driver_resolver import (
    DriverResolver
)

from app.wh.runtime.session_folder import (
    RuntimeSessionFolder
)
from app.wh.runtime.screenshots.screenshot_resolver import (
    ScreenshotResolver
)
from app.wh.runtime.vision.runtime_vision import (
    RuntimeVision
)

class RuntimeSession:

    def __init__(

        self,
        intent,
        mode
    ):

        detector = CanvasDetector()

        self.canvas_bounds = (
            detector.detect()
        )

        self.geometry = GeometryFactory.build(
            intent
        )

        self.folder = (
            RuntimeSessionFolder()
        )

        self.mouse = (
            DriverResolver.resolve_mouse()
        )

        self.waiters = RuntimeWaiters()

        self.screenshots = (
        ScreenshotResolver.resolve(
        self.folder
         )
        )

        self.screenshot_store = (
            ScreenshotStore()
        )

        self.hooks = RuntimeHooks()

        self.vision = RuntimeVision()

        self.mode = mode