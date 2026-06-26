from types import SimpleNamespace

from app.wh.runtime.construction_pipeline import (
    ConstructionPipeline
)

from app.wh.runtime.fields.field import (
    Field
)


def test_construction_pipeline():

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

    construction = (

        SimpleNamespace(

            topology=[

                [

                    f1,

                    f2

                ]

            ]

        )

    )

    pipeline = (

        ConstructionPipeline()

    )

    result = (

        pipeline.execute(

            construction

        )

    )

    assert len(

        result.actions

    ) == 1

    assert (

        result.actions[0].name

        == "frame"

    )