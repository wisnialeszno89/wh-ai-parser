from app.wh.runtime.vision.offer_validator import (
    OfferValidator
)

from app.wh.runtime.vision.offer_specification import (
    OfferSpecification
)

from app.wh.runtime.vision.products.window_product import (
    WindowProduct
)


def test_offer_validator():

    offer = OfferSpecification()

    offer.products.append(

        WindowProduct(

            quantity=2,

            profile="VEKA Softline 82 MD",

            outside_color="RAL7016",

            inside_color="RAL9016",

            glazing="Triple"

        )

    )

    validator = OfferValidator()

    errors = validator.validate(

        offer

    )

    assert errors == []