from app.wh.runtime.fields.field_geometry import (
    FieldGeometry
)


def test_field_geometry():

    geometry = FieldGeometry(

        center_x=550,

        center_y=700,

        width_ratio=0.5,

        height_ratio=1.0

    )

    assert geometry.center_x == 550

    assert geometry.center_y == 700

    assert geometry.width_ratio == 0.5

    assert geometry.height_ratio == 1.0