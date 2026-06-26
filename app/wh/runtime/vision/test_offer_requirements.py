from app.wh.runtime.vision.offer_requirements import (
    OfferRequirements
)


def test_offer_requirements():

    requirements = (

        OfferRequirements(

            windows=8,

            balcony_doors=2,

            outside_color="Anthracite",

            inside_color="White",

            glazing="Triple",

            security="RC2"

        )

    )

    assert requirements.windows == 8

    assert requirements.balcony_doors == 2

    assert requirements.outside_color == "Anthracite"

    assert requirements.security == "RC2"