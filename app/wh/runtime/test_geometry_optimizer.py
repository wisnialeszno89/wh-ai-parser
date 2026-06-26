from app.wh.runtime.geometry_optimizer import (
    GeometryOptimizer
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


def test_geometry_optimizer():

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

        GeometryOptimizer()

    )

    optimized = (

        optimizer.optimize(

            project

        )

    )

    assert (

        optimized.schema.division

        is True

    )

    assert (

        optimized.schema.division_type

        ==

        "vertical"

    )

    assert (

        optimized.schema.ratio_x

        ==

        [

            0.5

        ]

    )