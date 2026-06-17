from app.wh.runtime.fields.field import (
    Field
)

from app.wh.runtime.openings.opening_types import (
    TILT_TURN
)


def test_field():

    field = Field(

        id=1,

        x=550,

        y=700,

        opening=TILT_TURN

    )

    assert field.id == 1

    assert field.x == 550

    assert field.y == 700

    assert field.opening == TILT_TURN