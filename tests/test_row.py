from app.wh.model.row import (
    Row
)

from app.wh.model.segment import (
    Segment
)


def test_row():

    row = Row(

        segments=[

            Segment(

                kind="left",

                opening="fix"

            ),

            Segment(

                kind="right",

                opening="tilt_turn"

            )

        ]

    )

    assert len(

        row.segments

    ) == 2