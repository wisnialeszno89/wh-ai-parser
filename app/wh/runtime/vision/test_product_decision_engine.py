from app.wh.runtime.vision.product_decision_engine import (
    ProductDecisionEngine
)

from app.wh.runtime.vision.offer_requirements import (
    OfferRequirements
)


def test_product_decision_engine():

    engine = (

        ProductDecisionEngine()

    )

    requirements = (

        OfferRequirements(

            security="RC2",

            glazing="Triple"

        )

    )

    profile = (

        engine.choose_profile(

            requirements

        )

    )

    assert profile == "VEKA Softline 82 MD"