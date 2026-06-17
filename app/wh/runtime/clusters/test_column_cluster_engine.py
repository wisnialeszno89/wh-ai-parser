from app.wh.runtime.fields.field import (
    Field
)

from app.wh.runtime.clusters.column_cluster_engine import (
    ColumnClusterEngine
)


def test_column_cluster_engine():

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

    engine = ColumnClusterEngine()

    columns = engine.cluster(

        fields

    )

    assert len(

        columns

    ) == 2

    assert len(

        columns[0]

    ) == 2

    assert len(

        columns[1]

    ) == 2