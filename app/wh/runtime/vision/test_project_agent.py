from app.wh.runtime.vision.project_agent import (
    ProjectAgent
)

from app.wh.runtime.vision.vision_runtime import (
    VisionRuntime
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


def test_project_agent():

    runtime = (

        VisionRuntime()

    )

    agent = (

        ProjectAgent(

            runtime

        )

    )

    offer = (

        ConstructionOffer()

    )

    offer.security.rc2 = (

        True

    )

    offer.hardware.hidden_hinges = (

        True

    )

    project = (

        ConstructionProject(

            schema=ConstructionSchema(

                width=2000,

                height=1500,

                schema="RU"

            ),

            offer=offer

        )

    )

    result = (

        agent.execute(

            project

        )

    )

    assert (

        result

        is True

    )