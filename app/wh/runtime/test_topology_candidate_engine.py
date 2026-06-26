from app.wh.runtime.topology_candidate_engine import (
    TopologyCandidateEngine
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


def test_topology_candidate_engine():

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

        TopologyCandidateEngine()

    )

    candidates = (

        engine.generate(

            project

        )

    )

    assert len(

        candidates

    ) == 2

    assert (
    candidates[0]
    .notation
    ==
    "RU|FIX|RU"
)