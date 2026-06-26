from app.wh.runtime.field_region_builder import (
    FieldRegionBuilder
)

from app.wh.runtime.field import (
    Field
)

from app.wh.model.opening import (
    Opening
)


def test_field_region_builder():

    builder = FieldRegionBuilder()

    fields = [

        Field(

            id=1,

            x=550,

            y=700,

            opening=Opening.TILT_TURN

        )

    ]

    regions = builder.build(

        fields

    )

    region = regions[0]

    assert region.id == 1

    assert region.opening == (

        Opening.TILT_TURN

    )

    assert region.center_x == 550

    assert region.center_y == 700