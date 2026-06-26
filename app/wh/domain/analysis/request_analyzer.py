from app.wh.domain.analysis.missing_information import (
    MissingInformation
)

from app.wh.domain.analysis.request_analysis import (
    RequestAnalysis
)

from app.wh.domain.request.customer_request import (
    CustomerRequest
)


class RequestAnalyzer:

    REQUIRED_PRODUCT_FIELDS = (

        "category",

        "quantity",

        "glazing",

        "security",

        "outside_color",

        "inside_color"

    )

    def analyze(

        self,

        request: CustomerRequest

    ) -> RequestAnalysis:

        missing = MissingInformation()

        if not request.products:

            missing.add(

                "products"

            )

        for product in request.products:

            if not product.category:

                missing.add(

                    "category"

                )

            if product.quantity <= 0:

                missing.add(

                    "quantity"

                )

            if not product.glazing:

                missing.add(

                    "glazing"

                )

            if not product.security:

                missing.add(

                    "security"

                )

            if not product.outside_color:

                missing.add(

                    "outside_color"

                )

            if not product.inside_color:

                missing.add(

                    "inside_color"

                )

        return RequestAnalysis(

            request_complete=missing.is_complete,

            missing=missing

        )