from app.wh.runtime.vision.offer_schema import (
    OfferSchema
)


def test_offer_schema():

    offer = (

        OfferSchema(

            customer_name="Muller GmbH",

            profile="Softline82",

            color="Anthracite",

            addon="RC2"

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