from app.wh.runtime.vision.self_healing_execution_result import (
    SelfHealingExecutionResult
)


class SelfHealingExecutionPipeline:

    def __init__(

        self,

        brain

    ):

        self.brain = brain

    def execute(

        self,

        execution_result

    ):

        verification = (

            self.brain.execution_verification_pipeline.execute(

                execution_result

            )

        )

        retries_used = 0

        if not verification.success:

            retries_used = 1

            verification = (

                self.brain.execution_verification_pipeline.execute(

                    execution_result

                )

            )

        return (

            SelfHealingExecutionResult(

                success=verification.success,

                retries_used=retries_used,

                confidence=verification.confidence,

                message="self-healing completed"

            )

        )