from app.wh.runtime.vision.recovery_execution_result import (
    RecoveryExecutionResult
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_recovery_execution_result():

    result = (

        RecoveryExecutionResult(

            success=True,

            strategy=(

                AlternativeStrategy.OCR_FALLBACK

            )

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.strategy

        ==

        AlternativeStrategy.OCR_FALLBACK

    )