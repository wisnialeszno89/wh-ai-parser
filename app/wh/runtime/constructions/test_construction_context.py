from types import SimpleNamespace

from app.wh.runtime.fields.field import (
    Field
)

from app.wh.runtime.constructions.construction_context import (
    ConstructionContext
)


def test_construction_context():

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

    f4 = Field(

        id=4,

        x=1000,

        y=700

    )

    construction = (

        SimpleNamespace(

            fields=[

                f1,

                f2,

                f3,

                f4

            ],

            topology=[

                [f1, f2],

                [f3, f4]

            ]

        )

    )

    context = (

        ConstructionContext(

            construction

        )

    )

    assert (

        context.field(

            3

        ).id

        == 3

    )

    assert (

        context.top_left()

        .id

        == 1

    )

    assert (

        context.top_right()

        .id

        == 2

    )

    assert (

        context.bottom_left()

        .id

        == 3

    )

    assert (

        context.bottom_right()

        .id

        == 4

    )

    assert len(

        context.row(

            0

        )

    ) == 2

    assert len(

        context.column(

            1

        )

    ) == 2