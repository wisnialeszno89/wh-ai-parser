from app.runtime.execution.vision.models.vision_context import VisionContext


class CanvasPlacementResolver:
    """
    Resolves a safe point inside the currently observed canvas.

    The resolver deliberately uses the observed canvas bounds instead of
    fixed screen coordinates so different WindowHub layouts remain supported.
    """

    def resolve(
        self,
        vision: VisionContext,
    ) -> tuple[int, int]:

        if vision is None or vision.canvas is None:
            raise RuntimeError(
                "Canvas not available in current VisionContext"
            )

        bounds = vision.canvas.bounds

        if bounds.width <= 0 or bounds.height <= 0:
            raise RuntimeError(
                "Canvas has invalid bounds"
            )

        point = bounds.center

        print(
            f"[CANVAS] Placement point: {point}"
        )

        return point
