from app.request.request_analyzer import (
    RequestAnalyzer,
)

from app.wh.domain.customer.customer import (
    Customer,
)

from app.wh.domain.request.customer_request import (
    CustomerRequest,
)


def main():

    request = CustomerRequest(

        customer=Customer(),

    )

    analyzer = RequestAnalyzer()

    result = analyzer.analyze(

        request

    )

    print()

    print(

        "Completed:",

        result.completed,

    )

    print()

    print(

        "Missing:",

        result.missing,

    )

    print()

    print(

        "Warnings:",

        result.warnings,

    )


if __name__ == "__main__":

    main()