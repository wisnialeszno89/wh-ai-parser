from app.wh.runtime.fields.field import (
    Field
)

from app.wh.runtime.clusters.row_cluster_engine import (
    RowClusterEngine
)


def test_row_cluster_engine():

    fields = [

        Field(

            id=1,

            x=500,

            y=300

        ),

        Field(

            id=2,

            x=1000,

            y=300

        ),

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

    engine = RowClusterEngine()

    rows = engine.cluster(

        fields

    )

    assert len(

        rows

    ) == 2

    assert len(

        rows[0]

    ) == 2

    assert len(

        rows[1]

    ) == 2