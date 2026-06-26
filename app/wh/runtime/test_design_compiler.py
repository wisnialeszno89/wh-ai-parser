from app.wh.runtime.design_compiler import (
    DesignCompiler
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


def test_design_compiler():

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

    candidate = (

        TopologyCandidate(

            notation="RU|FIX|RU"

        )

    )

    compiler = (

        DesignCompiler()

    )

    schema = (

        compiler.compile(

            project,

            candidate

        )

    )

    assert (

        len(

            schema.segments

        )

        ==

        3

    )