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

    construction: Rect | None = None
