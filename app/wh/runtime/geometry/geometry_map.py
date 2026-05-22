from app.wh.runtime.canvas_target import (
    CanvasTarget
)


class GeometryMap:

    def __init__(self):

        self.targets = {

            CanvasTarget.CENTER:

                lambda bounds: (

                    (
                        bounds[0] +
                        bounds[2]
                    ) // 2,

                    (
                        bounds[1] +
                        bounds[3]
                    ) // 2
                ),

            CanvasTarget.FRAME:

                lambda bounds: (

                    (
                        bounds[0] +
                        bounds[2]
                    ) // 2,

                    bounds[1] + 120
                ),

            CanvasTarget.LEFT:

                lambda bounds: (

                    bounds[0] + int(

                        (
                            bounds[2] -
                            bounds[0]
                        ) * 0.25
                    ),

                    (
                        bounds[1] +
                        bounds[3]
                    ) // 2
                ),

            CanvasTarget.RIGHT:

                lambda bounds: (

                    bounds[0] + int(

                        (
                            bounds[2] -
                            bounds[0]
                        ) * 0.75
                    ),

                    (
                        bounds[1] +
                        bounds[3]
                    ) // 2
                ),

            CanvasTarget.MULLION:

                lambda bounds: (

                    (
                        bounds[0] +
                        bounds[2]
                    ) // 2,

                    (
                        bounds[1] +
                        bounds[3]
                    ) // 2
                ),

            CanvasTarget.SASH_LEFT:

                lambda bounds: (

                    bounds[0] + int(

                        (
                            bounds[2] -
                            bounds[0]
                        ) * 0.25
                    ),

                    (
                        bounds[1] +
                        bounds[3]
                    ) // 2
                ),

            CanvasTarget.SASH_RIGHT:

                lambda bounds: (

                    bounds[0] + int(

                        (
                            bounds[2] -
                            bounds[0]
                        ) * 0.75
                    ),

                    (
                        bounds[1] +
                        bounds[3]
                    ) // 2
                )
        }

    def resolve(

        self,
        target,
        bounds
    ):

        if target not in self.targets:

            raise RuntimeError(

                f"Missing target: "
                f"{target}"
            )

        resolver = self.targets[
            target
        ]

        return resolver(
            bounds
        )