from __future__ import annotations

from dataclasses import dataclass

from app.runtime.execution.vision.models.canvas import Canvas
from app.runtime.execution.vision.models.rect import Rect


@dataclass(slots=True)
class Workspace:
    """
    Main working area inside the WindowHub window.

    It contains all major UI regions used by the runtime.
    """

    bounds: Rect

    canvas: Canvas | None = None

    table: Rect | None = None

    right_panel: Rect | None = None

    notes: Rect | None = None