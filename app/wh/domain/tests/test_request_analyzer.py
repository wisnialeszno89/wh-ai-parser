from app.wh.domain.analysis.request_analyzer import (
    RequestAnalyzer
)

from app.wh.domain.customer.customer import (
    Customer
)

from app.wh.domain.product.product_request import (
    ProductRequest
)

from app.wh.domain.request.customer_request import (
    CustomerRequest
)


def test_request_analyzer_complete():

    request = CustomerRequest(

        customer=Customer(

            name="Muller"

        )

    )

    request.products.append(

        ProductRequest(

            category="window",

            quantity=8,

            glazing="Triple",

            security="RC2",

            outside_color="Anthracite",

            inside_color="White"

        )

    )

    analysis = (

        RequestAnalyzer().analyze(

            request

        )

    )

    assert analysis.request_complete

    assert analysis.missing.is_complete


def test_request_analyzer_missing_fields():

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

    analysis = (

        RequestAnalyzer().analyze(

            request

        )

    )

    assert not analysis.request_complete

    assert "glazing" in analysis.missing.fields

    assert "security" in analysis.missing.fields

    assert "outside_color" in analysis.missing.fields

    assert "inside_color" in analysis.missing.fields