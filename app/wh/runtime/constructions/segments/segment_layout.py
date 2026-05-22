from app.wh.runtime.constructions.segments.segment import (
    Segment
)

from app.wh.runtime.constructions.segments.segment_kind import (
    SegmentKind
)


class SegmentLayout:

    @staticmethod
    def fix_ru():

        return [

            Segment(

                SegmentKind.FIX,

                0.7
            ),

            Segment(

                SegmentKind.RU,

                0.3
            )
        ]