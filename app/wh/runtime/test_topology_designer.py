from app.wh.runtime.topology_designer import (
    TopologyDesigner
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


def test_topology_designer():

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

    designer = (

        TopologyDesigner()

    )

    result = (

        designer.design(

            project

        )

    )

    assert (
    result.notation
    ==
    "RU|FIX|RU"
    )

    assert (

        result.score

        ==

        0.95

    )