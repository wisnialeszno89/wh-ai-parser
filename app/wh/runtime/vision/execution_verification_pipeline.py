from app.wh.runtime.vision.execution_verification_result import (
    ExecutionVerificationResult
)


class ExecutionVerificationPipeline:

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

            self.brain.offer_verification_engine.verify(

                execution_result

            )

        )

        screenshot = (

            self.brain.screenshot_comparison_engine.compare(

                "expected",

                "expected"

            )

        )

        confidence = (

            verification.confidence

            *

            screenshot.confidence

        )

        return (

            ExecutionVerificationResult(

                success=(

                    verification.success

                    and

                    screenshot.success

                ),

                confidence=confidence,

                message="execution verified"

            )

        )