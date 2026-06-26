from app.wh.runtime.vision.intelligent_project_agent import (
    IntelligentProjectAgent
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
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


def test_intelligent_project_agent():

    runtime = (

        VisionRuntime()

    )

    brain = (

        ProjectBrain()

    )

    agent = (

        IntelligentProjectAgent(

            runtime,

            brain

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

    assert (

        agent.execute(

            project

        )

        is True

    )

    assert (

        brain.goal_memory.contains(

            "enable_rc2"

        )

        is True

    )

    assert (

        brain.goal_memory.contains(

            "enable_hidden_hinges"

        )

        is True

    )