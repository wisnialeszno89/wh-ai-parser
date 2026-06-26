from app.wh.domain.product.product_request import (
    ProductRequest
)


def test_product_request():

    product = ProductRequest(

        category="window",

        quantity=8

    )

    assert product.category == "window"

    assert product.quantity == 8