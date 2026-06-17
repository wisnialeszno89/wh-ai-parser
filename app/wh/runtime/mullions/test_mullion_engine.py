from app.wh.runtime.mullions.mullion_engine import (
    MullionEngine
)

from app.wh.runtime.fields.field import (
    Field
)


def test_mullion_engine():

    engine = MullionEngine()

    fields = [

        Field(

            id=1,

            x=500,

            y=700

        ),

        Field(

            id=2,

            x=1000,

            y=700

        ),

        Field(

            id=3,

            x=1500,

            y=700

        )

    ]

    result = engine.calculate(

        fields

    )

    assert len(

        result

    ) == 2

    assert (

        result[0]

        .left_field

        .id

        == 1

    )

    assert (

        result[0]

        .right_field

        .id

        == 2

    )

    assert (

        result[1]

        .left_field

        .id

        == 2

    )

    assert (

        result[1]

        .right_field

        .id

        == 3

    )