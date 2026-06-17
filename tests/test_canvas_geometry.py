from app.wh.runtime.canvas_geometry import (
    CanvasGeometry
)


def test_canvas_geometry():

    canvas = CanvasGeometry(

        left=100,

        top=200,

        right=1600,

        bottom=1200

    )

    assert canvas.center_x == 850

    assert canvas.center_y == 700