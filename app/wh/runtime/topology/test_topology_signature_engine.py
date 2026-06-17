from types import SimpleNamespace

from app.wh.runtime.fields.field import (
    Field
)

from app.wh.runtime.topology.topology_signature_engine import (
    TopologySignatureEngine
)


def test_topology_signature_engine():

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

            topology=[

                [f1, f2],

                [f3, f4]

            ]

        )

    )

    signature = (

        TopologySignatureEngine()

        .build(

            construction

        )

    )

    assert signature.rows == 2

    assert signature.columns == 2

    assert signature.balanced is True

    assert signature.single_row is False

    assert signature.single_column is False