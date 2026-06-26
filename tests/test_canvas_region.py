from app.wh.vision.canvas_region import (
    CanvasRegion
)


def test_canvas_region():

    canvas = CanvasRegion(

        left=100,

        top=200,

        right=1600,

        bottom=1200

    )

    assert canvas.width == 1500

    assert canvas.height == 1000

    assert canvas.center_x == 850

    assert canvas.center_y == 700