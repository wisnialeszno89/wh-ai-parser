from app.wh.runtime.canvas_locator import (
    CanvasLocator
)


def test_canvas_locator():

    locator = CanvasLocator()

    canvas = locator.locate()

    assert canvas.center_x == 850

    assert canvas.center_y == 700