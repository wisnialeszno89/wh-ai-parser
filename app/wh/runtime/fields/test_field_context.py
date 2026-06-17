from app.wh.runtime.fields.field import (
    Field
)

from app.wh.runtime.fields.field_context import (
    FieldContext
)

from app.wh.runtime.topology.topology_context import (
    TopologyContext
)


def test_field_context():

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

    topology = [

        [f1, f2],

        [f3, f4]

    ]

    topology_context = (

        TopologyContext(

            topology

        )

    )

    field_context = (

        FieldContext(

            f1,

            topology_context

        )

    )

    assert (

        field_context.right()

        .id

        == 2

    )

    assert (

        field_context.bottom()

        .id

        == 3

    )

    assert (

        field_context.left()

        is None

    )

    assert (

        field_context.top()

        is None

    )