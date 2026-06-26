from app.wh.runtime.vision.project_execution_result import (
    ProjectExecutionResult
)

from app.wh.runtime.vision.offer_execution_result import (
    OfferExecutionResult
)


def test_project_execution_result():

    result = (

        ProjectExecutionResult(

            offer_result=OfferExecutionResult()

        )

    )

    assert (

        result.offer_result

        is not None

    )

    assert (

        result.status

        is None

    )