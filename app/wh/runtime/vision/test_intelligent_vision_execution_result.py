from app.wh.runtime.vision.intelligent_vision_execution_result import (
    IntelligentVisionExecutionResult
)


def test_intelligent_vision_execution_result():

    result = (

        IntelligentVisionExecutionResult(

            success=True,

            message="offer executed"

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.message

        ==

        "offer executed"

    )