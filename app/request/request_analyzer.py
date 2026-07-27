from app.request.analysis_result import (
    AnalysisResult,
)
from app.wh.domain.request.customer_request import (
    CustomerRequest,
)


class RequestAnalyzer:

    def analyze(

        self,

        request: CustomerRequest,

    ) -> AnalysisResult:

        result = AnalysisResult()

        #
        # Czy są produkty?
        #

        if len(request.products) == 0:

            result.missing.append(

                "products"

            )

        #
        # Czy znamy język?
        #

        if request.language == "":

            result.warnings.append(

                "language"

            )

        result.completed = (

            len(result.missing) == 0

        )

        return result