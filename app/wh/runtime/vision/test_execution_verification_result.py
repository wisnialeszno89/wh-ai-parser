from app.wh.runtime.vision.execution_verification_result import (
    ExecutionVerificationResult
)


def test_execution_verification_result():

    result = (

        ExecutionVerificationResult(

            success=True,

            confidence=0.98,

            message="verified"

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.confidence

        ==

        0.98

    )