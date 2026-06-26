from app.wh.runtime.vision.recovery_execution_result import (
    RecoveryExecutionResult
)


class RecoveryExecutor:

    def execute(

        self,

        plan

    ):

        return (

            RecoveryExecutionResult(

                success=True,

                strategy=plan.strategy

            )

        )