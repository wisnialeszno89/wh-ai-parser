from app.wh.runtime.canvas_target import (
    CanvasTarget
)

from app.wh.runtime.constructions.segments.segment_kind import (
    SegmentKind
)


class SegmentTargetResolver:

    @staticmethod
    def resolve(

        index,
        segment
    ):

        if index == 0:

            return CanvasTarget.LEFT

        if index == 1:

            return CanvasTarget.RIGHT

        return CanvasTarget.CENTER