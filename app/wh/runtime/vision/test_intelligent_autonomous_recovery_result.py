from app.wh.runtime.vision.intelligent_autonomous_recovery_result import (
    IntelligentAutonomousRecoveryResult
)

from app.wh.runtime.vision.rollback_result import (
    RollbackResult
)

from app.wh.runtime.vision.recovery_execution_result import (
    RecoveryExecutionResult
)

from app.wh.runtime.vision.alternative_strategy import (
    AlternativeStrategy
)


def test_intelligent_autonomous_recovery_result():

    result = (

        IntelligentAutonomousRecoveryResult(

            rollback_result=(

                RollbackResult(

                    success=True

                )

            ),

            recovery_result=(

                RecoveryExecutionResult(

                    success=True,

                    strategy=(

                        AlternativeStrategy.OCR_FALLBACK

                    )

                )

            ),

            success=True

        )

    )

    assert (

        result.success

        is True

    )