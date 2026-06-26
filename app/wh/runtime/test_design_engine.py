from app.wh.runtime.design_engine import (
    DesignEngine
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


def test_design_engine():

    project = (

        ConstructionProject(

            schema=ConstructionSchema(

                width=5000,

                height=1400,

                schema="FIX"

            ),

            offer=ConstructionOffer()

        )

    )

    engine = (

        DesignEngine()

    )

    report = (

        engine.design(

            project

        )

    )

    assert (
    report.winner.notation
    ==
    "RU|FIX|RU"
    )

    assert (

        len(

            report.candidates

        )

        ==

        2

    )

    assert (

        report.candidates[0]

        .score

        >=

        report.candidates[1]

        .score

    )