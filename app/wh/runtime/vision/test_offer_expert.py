from app.wh.runtime.vision.offer_expert import (
    OfferExpert
)

from app.wh.runtime.vision.offer_requirements import (
    OfferRequirements
)


def test_offer_expert():

    expert = OfferExpert()

    requirements = OfferRequirements(

        windows=8,

        outside_color="Anthracite",

        inside_color="White",

        glazing="Triple",

        security="RC2"

    )

    specification = expert.build_offer(

        requirements

    )

    assert len(

        specification.products

    ) == 1

    product = specification.products[0]

    assert product.quantity == 8

    assert product.profile == "VEKA Softline 82 MD"

    assert product.security == "RC2"