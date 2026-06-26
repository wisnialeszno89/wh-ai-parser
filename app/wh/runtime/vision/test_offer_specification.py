from app.wh.runtime.vision.offer_specification import (
    OfferSpecification
)

from app.wh.runtime.vision.products.window_product import (
    WindowProduct
)


def test_offer_specification():

    offer = OfferSpecification()

    offer.products.append(

        WindowProduct(

            quantity=5

        )

    )

    assert len(offer.products) == 1

    assert offer.products[0].quantity == 5