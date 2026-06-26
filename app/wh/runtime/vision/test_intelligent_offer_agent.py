from app.wh.runtime.vision.intelligent_offer_agent import (
    IntelligentOfferAgent
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


def test_intelligent_offer_agent():

    runtime = (

        VisionRuntime()

    )

    brain = (

        ProjectBrain()

    )

    agent = (

        IntelligentOfferAgent(

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

    assert (

        agent.execute(

            offer

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

    count = (

        len(

            brain.goal_memory.completed

        )

    )

    assert (

        agent.execute(

            offer

        )

        is True

    )

    assert (

        len(

            brain.goal_memory.completed

        )

        ==

        count

    )