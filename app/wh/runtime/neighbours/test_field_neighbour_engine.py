from app.wh.runtime.fields.field import (
    Field
)

from app.wh.runtime.mullions.mullion import (
    Mullion
)

from app.wh.runtime.transoms.transom import (
    Transom
)

from app.wh.runtime.neighbours.field_neighbour_engine import (
    FieldNeighbourEngine
)


def test_field_neighbour_engine():

    f1 = Field(

        id=1,

        x=500,

        y=300

    )

    f2 = Field(

        id=2,

        x=1000,

        y=300

    )

    f3 = Field(

        id=3,

        x=500,

        y=700

    )

    mullions = [

        Mullion(

            left_field=f1,

            right_field=f2

        )

    ]

    transoms = [

        Transom(

            top_field=f1,

            bottom_field=f3

        )

    ]

    engine = FieldNeighbourEngine()

    assert (

        engine.right(

            f1,

            mullions

        ).id

        == 2

    )

    assert (

        engine.left(

            f2,

            mullions

        ).id

        == 1

    )

    assert (

        engine.bottom(

            f1,

            transoms

        ).id

        == 3

    )

    assert (

        engine.top(

            f3,

            transoms

        ).id

        == 1

    )