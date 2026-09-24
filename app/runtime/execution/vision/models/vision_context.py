from dataclasses import dataclass, field

from app.runtime.execution.window.window_rect import WindowRect
from app.wh.vision.screenshot import Screenshot

from app.runtime.execution.vision.models.canvas import Canvas
from app.runtime.execution.vision.models.rect import Rect
from app.runtime.execution.vision.models.logical_object import LogicalObject
from app.runtime.execution.vision.models.logical_object_graph import LogicalObjectGraph


@dataclass(slots=True)
class VisionContext:

    window: WindowRect

    screenshot: Screenshot

    toolbar: object | None = None

    controls: list = None

    logical_objects: list[LogicalObject] = field(default_factory=list)
    logical_object_graph: LogicalObjectGraph | None = None

    scene_graph: object | None = None

    canvas: Canvas | None = None

    construction: Rect | None = None
