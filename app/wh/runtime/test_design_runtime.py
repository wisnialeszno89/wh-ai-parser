from unittest.mock import (
    MagicMock
)

from app.wh.runtime.design_runtime import (
    DesignRuntime
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


def test_design_runtime():

    runtime = (

        DesignRuntime()

    )

    runtime.executor = (

        MagicMock()

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

    construction = (

        runtime.execute(

            project

        )

    )

    assert (

        len(

            construction.fields

        )

        > 0

    )