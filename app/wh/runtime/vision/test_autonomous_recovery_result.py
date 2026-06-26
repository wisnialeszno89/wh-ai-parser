from app.wh.runtime.vision.autonomous_recovery_result import (
    AutonomousRecoveryResult
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


def test_autonomous_recovery_result():

    result = (

        AutonomousRecoveryResult(

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