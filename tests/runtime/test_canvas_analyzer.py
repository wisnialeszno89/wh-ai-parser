import cv2
import numpy as np

from types import SimpleNamespace

from app.runtime.execution.vision.analyzers.canvas_analyzer import (
    CanvasAnalyzer,
)


class FakeScreenshot:
    def __init__(self, image):
        self.image = image
        self.width = image.shape[1]
        self.height = image.shape[0]


class FakeBounds:
    bottom = 100


class FakeContext:
    def __init__(self, image):
        self.screenshot = FakeScreenshot(image)
        self.toolbar = SimpleNamespace(bounds=FakeBounds())
        self.canvas = None


def test_canvas_analyzer_detects_bordered_workspace():
    image = np.full((500, 800, 3), 240, dtype=np.uint8)

    cv2.rectangle(
        image,
        (60, 180),
        (300, 420),
        (40, 40, 40),
        2,
    )

    context = FakeContext(image)

    result = CanvasAnalyzer().analyze(context)

    assert result.canvas is not None

    bounds = result.canvas.bounds

    assert bounds.x <= 65
    assert bounds.y <= 185
    assert bounds.width >= 230
    assert bounds.height >= 230


def test_canvas_analyzer_keeps_movable_workspace_geometry():
    image = np.full((600, 900, 3), 240, dtype=np.uint8)

    cv2.rectangle(
        image,
        (420, 240),
        (760, 500),
        (40, 40, 40),
        2,
    )

    context = FakeContext(image)

    result = CanvasAnalyzer().analyze(context)

    bounds = result.canvas.bounds

    assert bounds.x <= 425
    assert bounds.y <= 245
    assert bounds.width >= 250
    assert bounds.height >= 250
