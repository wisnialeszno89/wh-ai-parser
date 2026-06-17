from app.wh.runtime.field_action_planner import (
    FieldActionPlanner
)

from app.wh.runtime.fields.field import (
    Field
)

from app.wh.runtime.openings.opening_types import (
    TILT_TURN,
    FIX
)


def test_field_action_planner():

    planner = FieldActionPlanner()

    fields = [

        Field(

            id=1,

            x=550,

            y=700,

            opening=TILT_TURN

        ),

        Field(

            id=2,

            x=1150,

            y=700,

            opening=FIX

        )

    ]

    result = planner.plan(

        fields

    )

    assert (

        result[0]

        .actions[0]

        .name

        ==

        "frame"

    )

    assert (

        result[0]

        .actions[1]

        .name

        ==

        "sash"

    )

    assert (

        result[0]

        .actions[2]

        .name

        ==

        "glass"

    )

    assert (

        result[1]

        .actions[0]

        .name

        ==

        "frame"

    )

    assert (

        result[1]

        .actions[1]

        .name

        ==

        "glass"

    )