from types import SimpleNamespace

from app.wh.runtime.construction_pipeline import (
    ConstructionPipeline
)

from app.wh.runtime.fields.field import (
    Field
)


def test_pipeline_to_action_plan():

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

    plan = (

        pipeline.execute(

            construction

        )

    )

    assert (

        plan.count()

        == 1

    )