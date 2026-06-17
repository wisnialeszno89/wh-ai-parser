from app.wh.runtime.transoms.transom_engine import (
    TransomEngine
)

from app.wh.runtime.fields.field import (
    Field
)


def test_transom_engine():

    engine = TransomEngine()

    top_fields = [

        Field(

            id=1,

            x=500,

            y=300

        ),

        Field(

            id=2,

            x=1000,

            y=300

        )

    ]

    bottom_fields = [

        Field(

            id=3,

            x=500,

            y=700

        ),

        Field(

            id=4,

            x=1000,

            y=700

        )

    ]

    result = engine.calculate(

        top_fields,

        bottom_fields

    )

    assert len(

        result

    ) == 2

    assert (

        result[0]

        .top_field

        .id

        == 1

    )

    assert (

        result[0]

        .bottom_field

        .id

        == 3

    )

    assert (

        result[1]

        .top_field

        .id

        == 2

    )

    assert (

        result[1]

        .bottom_field

        .id

        == 4

    )