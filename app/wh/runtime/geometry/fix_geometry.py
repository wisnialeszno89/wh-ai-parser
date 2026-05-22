from app.wh.runtime.geometry.geometry_map import (
    GeometryMap
)

from app.wh.runtime.canvas_target import (
    CanvasTarget
)


def build_fix_geometry():

    geometry = GeometryMap()

    geometry.set_target(
        CanvasTarget.CENTER,
        (0.5, 0.5)
    )

    geometry.set_target(
        CanvasTarget.FRAME,
        (0.5, 0.15)
    )

    geometry.set_target(
        CanvasTarget.GLASS,
        (0.5, 0.5)
    )

    return geometry