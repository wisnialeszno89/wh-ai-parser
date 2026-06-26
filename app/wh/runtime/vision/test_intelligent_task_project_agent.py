from app.wh.runtime.vision.intelligent_task_project_agent import (
    IntelligentTaskProjectAgent
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


def test_intelligent_task_project_agent():

    runtime = (

        VisionRuntime()

    )

    brain = (

        ProjectBrain()

    )

    agent = (

        IntelligentTaskProjectAgent(

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

    result = (

        agent.execute(

            project

        )

    )

    assert (

        len(

            result.offer_result.task_results

        )

        ==

        2

    )