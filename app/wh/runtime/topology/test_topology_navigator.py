from app.wh.runtime.fields.field import (
    Field
)

from app.wh.runtime.topology.topology_navigator import (
    TopologyNavigator
)


def test_topology_navigator():

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

    navigator = (

        TopologyNavigator()

    )

    assert (

        navigator.right(

            topology,

            f1

        ).id

        == 2

    )

    assert (

        navigator.left(

            topology,

            f2

        ).id

        == 1

    )

    assert (

        navigator.bottom(

            topology,

            f1

        ).id

        == 3

    )

    assert (

        navigator.top(

            topology,

            f3

        ).id

        == 1

    )

    assert (

        navigator.left(

            topology,

            f1

        )

        is None

    )

    assert (

        navigator.top(

            topology,

            f1

        )

        is None

    )