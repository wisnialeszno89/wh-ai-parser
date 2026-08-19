from dataclasses import dataclass

from app.runtime.execution.window.window_rect import WindowRect
from app.wh.vision.screenshot import Screenshot

from app.runtime.execution.vision.models.canvas import Canvas
from app.runtime.execution.vision.models.rect import Rect


@dataclass(slots=True)
class VisionContext:

    window: WindowRect

    screenshot: Screenshot

    toolbar: object | None = None

    controls: list = None

    scene_graph: object | None = None

    canvas: Canvas | None = None

    # Bounding box of the actual finished WindowHub construction, when one is
    # visible. This is deliberately separate from canvas because the canvas is
    # the editable work area, not the object itself.
    construction: Rect | None = None
