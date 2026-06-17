from app.wh.runtime.fields.field import (
    Field
)

from app.wh.runtime.topology.grid_topology_engine import (
    GridTopologyEngine
)


def test_grid_topology_engine():

    fields = [

        Field(

            id=4,

            x=1000,

            y=700

        ),

        Field(

            id=2,

            x=1000,

            y=300

        ),

        Field(

            id=1,

            x=500,

            y=300

        ),

        Field(

            id=3,

            x=500,

            y=700

        )

    ]

    topology = (

        GridTopologyEngine()

        .build(

            fields

        )

    )

    assert (

        topology[0][0].id

        == 1

    )

    assert (

        topology[0][1].id

        == 2

    )

    assert (

        topology[1][0].id

        == 3

    )

    assert (

        topology[1][1].id

        == 4

    )