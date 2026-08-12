from types import SimpleNamespace

import pytest

from app.runtime.execution.canvas_placement_resolver import (
    CanvasPlacementResolver,
)
from app.runtime.execution.vision.models.rect import Rect


def test_canvas_placement_uses_observed_canvas_center():
    vision = SimpleNamespace(
        canvas=SimpleNamespace(
            bounds=Rect(
                x=200,
                y=100,
                width=1000,
                height=600,
            )
        )
    )

    point = CanvasPlacementResolver().resolve(
        vision,
    )

    assert point == (700, 400)


def test_canvas_placement_requires_canvas():
    vision = SimpleNamespace(
        canvas=None,
    )

    with pytest.raises(RuntimeError, match="Canvas not available"):
        CanvasPlacementResolver().resolve(
            vision,
        )
