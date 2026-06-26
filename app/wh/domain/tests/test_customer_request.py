from app.wh.domain.customer.customer import Customer

from app.wh.domain.product.product_request import (
    ProductRequest
)

from app.wh.domain.request.customer_request import (
    CustomerRequest
)


def test_customer_request():

    request = CustomerRequest(

        customer=Customer(

            name="Muller"

        )

    )

    request.products.append(

        ProductRequest(

            category="window",

            quantity=8

        )

    )

    assert request.customer.name == "Muller"

    assert len(request.products) == 1