from app.wh.runtime.topology_scoring_engine import (
    TopologyScoringEngine
)

from app.wh.runtime.topology_candidate import (
    TopologyCandidate
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


def test_topology_scoring_engine():

    candidate = (

        TopologyCandidate(

            notation="RU|FIX|RU"

        )

    )

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

        TopologyScoringEngine()

    )

    result = (

        engine.score(

            candidate,

            project

        )

    )

    assert (

        result.score

        ==

        0.95

    )