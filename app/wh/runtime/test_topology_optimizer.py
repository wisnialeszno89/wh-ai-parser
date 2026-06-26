from app.wh.runtime.topology_optimizer import (
    TopologyOptimizer
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


def test_topology_optimizer():

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

    optimizer = (

        TopologyOptimizer()

    )

    suggestions = (

        optimizer.suggest(

            project

        )

    )

    assert (

        suggestions[0]

        .notation

        ==

        "RU+FIX+RU"

    )