from app.wh.runtime.segments.segment import (
    Segment
)

from app.wh.runtime.openings.opening_types import (
    TILT_TURN
)


def test_segment():

    segment = Segment(

        opening=TILT_TURN,

        width_ratio=0.5,

        height_ratio=1.0

    )

    assert segment.opening == TILT_TURN

    assert segment.width_ratio == 0.5

    assert segment.height_ratio == 1.0