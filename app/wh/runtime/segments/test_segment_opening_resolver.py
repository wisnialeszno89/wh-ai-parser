from app.wh.runtime.segments.segment import (
    Segment
)

from app.wh.runtime.segments.segment_opening_resolver import (
    SegmentOpeningResolver
)

from app.wh.runtime.openings.opening_types import (
    TILT_TURN,
    FIX
)


def test_segment_opening_resolver():

    resolver = SegmentOpeningResolver()

    segments = [

        Segment(

            opening=TILT_TURN,

            width_ratio=0.5

        ),

        Segment(

            opening=FIX,

            width_ratio=0.5

        )

    ]

    result = resolver.resolve(

        segments

    )

    assert result == [

        TILT_TURN,

        FIX

    ]