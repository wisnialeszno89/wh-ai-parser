from app.wh.runtime.vision.offer_builder import (
    OfferBuilder
)

from app.wh.runtime.vision.customer_prediction import (
    CustomerPrediction
)


def test_offer_builder():

    prediction = (

        CustomerPrediction(

            customer_name="Muller GmbH",

            profile="Softline82",

            color="Anthracite",

            addon="RC2",

            confidence=0.91

        )

    )

    builder = (

        OfferBuilder()

    )

    offer = (

        builder.build(

            prediction

        )

    )

    assert (

        offer.customer_name

        ==

        "Muller GmbH"

    )

    assert (

        offer.profile

        ==

        "Softline82"

    )

    assert (

        offer.color

        ==

        "Anthracite"

    )

    assert (

        offer.addon

        ==

        "RC2"

    )