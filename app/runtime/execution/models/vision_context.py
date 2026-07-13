print("OLD VisionContext")
from __future__ import annotations

from dataclasses import dataclass

from app.wh.vision.screenshot import Screenshot


@dataclass(slots=True)
class VisionContext:
    """
    Carries data through the Vision Pipeline.

    Each analyzer enriches this context with new information.
    """

    window: object

    screenshot: Screenshot

    toolbar: object | None = None

    controls: list | None = None

    scene_graph: object | None = None