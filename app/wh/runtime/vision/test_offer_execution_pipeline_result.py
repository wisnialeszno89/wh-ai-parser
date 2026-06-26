from app.wh.runtime.vision.offer_execution_pipeline_result import (
    OfferExecutionPipelineResult
)

from app.wh.runtime.vision.intelligent_vision_execution_result import (
    IntelligentVisionExecutionResult
)


def test_offer_execution_pipeline_result():

    result = (

        OfferExecutionPipelineResult(

            execution_result=(

                IntelligentVisionExecutionResult(

                    success=True,

                    message="offer executed"

                )

            )

        )

    )

    assert (

        result.execution_result.success

        is True

    )