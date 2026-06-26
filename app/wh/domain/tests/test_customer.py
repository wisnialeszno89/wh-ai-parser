from app.wh.domain.customer.customer import Customer


def test_customer():

    customer = Customer(

        name="Muller GmbH",

        language="de"

    )

    assert customer.name == "Muller GmbH"

    assert customer.language == "de"