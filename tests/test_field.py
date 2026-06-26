from app.wh.runtime.field import (
    Field
)

from app.wh.model.opening import (
    Opening
)


def test_field():

    field = Field(

        id=1,

        x=550,

        y=700,

        opening=Opening.TILT_TURN

    )

    assert field.id == 1

    assert field.x == 550

    assert field.y == 700

    assert field.opening == Opening.TILT_TURN