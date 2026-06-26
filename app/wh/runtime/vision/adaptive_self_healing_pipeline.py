from app.wh.runtime.vision.adaptive_self_healing_result import (
    AdaptiveSelfHealingResult
)


class AdaptiveSelfHealingPipeline:

    def __init__(

        self,

        brain

    ):

        self.brain = brain

    def execute(

        self,

        execution_result,

        failure_reason="OCR_ERROR"

    ):

        verification = (

            self.brain.execution_verification_pipeline.execute(

                execution_result

            )

        )

        retries_used = 0

        if not verification.success:

            retries_used = 1

            recovery = (

                self.brain.adaptive_recovery_engine.recover(

                    self.brain,

                    failure_reason

                )

            )

            verification = (

                self.brain.execution_verification_pipeline.execute(

                    execution_result

                )

            )

        return (

            AdaptiveSelfHealingResult(

                success=(

                    verification.success

                ),

                retries_used=retries_used,

                confidence=(

                    verification.confidence

                ),

                message="adaptive self-healing completed"

            )

        )