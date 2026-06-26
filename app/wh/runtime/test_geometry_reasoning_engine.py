from app.wh.runtime.geometry_reasoning_engine import (
    GeometryReasoningEngine
)

from app.wh.runtime.construction_project import (
    ConstructionProject
)

from app.wh.runtime.construction_offer import (
    ConstructionOffer
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)


def test_geometry_reasoning_engine():

    project = (

        ConstructionProject(

            schema=ConstructionSchema(

                width=5000,

                height=1400,

                schema="RU+FIX+RU"

            ),

            offer=ConstructionOffer()

        )

    )

    engine = (

        GeometryReasoningEngine()

    )

    problems = (

        engine.validate(

            project

        )

    )

    assert len(

        problems

    ) == 1

    assert (

        problems[0]

        .code

        ==

        "WIDTH_EXCEEDED"

    )