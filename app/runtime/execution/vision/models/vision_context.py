from __future__ import annotations

from dataclasses import dataclass

from app.wh.vision.screenshot import (
    Screenshot,
)


@dataclass(slots=True)
class VisionContext:
    """
    Carries data through the Vision Pipeline.

    Each analyzer enriches this context with new information.

    The fields intentionally remain typed as integration-neutral objects
    where the legacy vision pipeline owns the concrete implementation.
    This keeps the context compatible with the existing analyzers while
    allowing the Universal Agent Core to consume the resulting artifacts.
    """

    window: object

    screenshot: Screenshot

    toolbar: object | None = None

    canvas: object | None = None

    construction: object | None = None

    controls: list | None = None

    logical_objects: list | None = None

    tracked_objects: list | None = None

    logical_object_graph: object | None = None

    scene_graph: object | None = None
