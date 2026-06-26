from app.wh.runtime.construction_project import (
    ConstructionProject
)

from app.wh.runtime.construction_offer import (
    ConstructionOffer
)

from app.wh.runtime.construction_schema import (
    ConstructionSchema
)

from app.wh.runtime.geometry_engine import (
    GeometryEngine
)


def test_geometry_engine():

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

    report = (

        GeometryEngine()

        .analyze(

            project

        )

    )

    assert (

        len(

            report.problems

        )

        == 1

    )