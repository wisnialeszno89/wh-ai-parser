from app.wh.runtime.vision.intelligent_task_offer_agent import (
    IntelligentTaskOfferAgent
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.vision_runtime import (
    VisionRuntime
)

from app.wh.runtime.construction_offer import (
    ConstructionOffer
)


def test_intelligent_task_offer_agent():

    runtime = (

        VisionRuntime()

    )

    brain = (

        ProjectBrain()

    )

    agent = (

        IntelligentTaskOfferAgent(

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

    result = (

        agent.execute(

            offer

        )

    )

    assert (

        len(

            result.task_results

        )

        ==

        2

    )

    assert (

        result.task_results[0].task_name

        ==

        "configure_security"

    )