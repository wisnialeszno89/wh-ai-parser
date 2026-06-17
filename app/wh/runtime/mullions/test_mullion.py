from app.wh.runtime.mullions.mullion import (
    Mullion
)


def test_mullion():

    mullion = Mullion(

        left_field=0,

        right_field=1

    )

    assert mullion.left_field == 0

    assert mullion.right_field == 1