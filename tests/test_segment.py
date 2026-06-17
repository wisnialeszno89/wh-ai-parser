from app.wh.model.segment import (
    Segment
)


def test_segment():

    segment = Segment(

        kind="left",

        opening="tilt_turn"

    )

    assert segment.kind == "left"

    assert segment.opening == "tilt_turn"