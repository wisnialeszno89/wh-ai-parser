from app.wh.runtime.vision.offer_agent import (
    OfferAgent
)

from app.wh.runtime.vision.vision_runtime import (
    VisionRuntime
)

from app.wh.runtime.construction_offer import (
    ConstructionOffer
)


def test_offer_agent():

    runtime = (

        VisionRuntime()

    )

    agent = (

        OfferAgent(

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

    result = (

        agent.execute(

            offer

        )

    )

    assert (

        result

        is True

    )