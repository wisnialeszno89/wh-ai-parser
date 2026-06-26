from app.wh.runtime.vision.products.window_product import (
    WindowProduct
)


def test_window_product():

    product = WindowProduct(

        quantity=3,

        width=1500,

        height=1400,

        outside_color="RAL7016",

        inside_color="RAL9016",

        security="RC2"

    )

    assert product.quantity == 3

    assert product.width == 1500

    assert product.security == "RC2"