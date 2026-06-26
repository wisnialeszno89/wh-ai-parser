from app.wh.vision.field_region import (
    FieldRegion
)

from app.wh.model.opening import (
    Opening
)


def test_field_region():

    field = FieldRegion(

        left=100,

        top=200,

        right=800,

        bottom=700,

        id=1,

        opening=Opening.TILT_TURN

    )

    assert field.width == 700

    assert field.height == 500

    assert field.center_x == 450

    assert field.center_y == 450

    assert field.id == 1

    assert field.opening == Opening.TILT_TURN