from app.construction.models.field import Field
from app.construction.models.opening import Opening
from app.construction.models.opening_type import OpeningType
from app.construction.models.opening_direction import OpeningDirection


def test_create_field():

    field = Field(

        opening=Opening(

            type=OpeningType.TILT_TURN,

            direction=OpeningDirection.RIGHT
        ),

        width=1300,

        height=1500
    )

    assert field.opening.type == OpeningType.TILT_TURN

    assert field.opening.direction == OpeningDirection.RIGHT