from app.wh.runtime.vision.offer_execution_result import (
    OfferExecutionResult
)

from app.wh.runtime.vision.task_execution_result import (
    TaskExecutionResult
)


def test_offer_execution_result():

    result = (

        OfferExecutionResult()

    )

    result.task_results.append(

        TaskExecutionResult(

            "configure_security"

        )

    )

    assert (

        len(

            result.task_results

        )

        ==

        1

    )