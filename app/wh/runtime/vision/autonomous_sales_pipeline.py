from app.wh.runtime.vision.autonomous_sales_result import (
    AutonomousSalesResult
)


class AutonomousSalesPipeline:

    def __init__(

        self,

        brain

    ):

        self.brain = brain

    def execute(

        self,

        mail_text

    ):

        offer_result = (

            self.brain.mail_to_offer_pipeline.execute(

                mail_text

            )

        )

        execution_result = (

            self.brain.offer_execution_pipeline.execute(

                offer_result.offer

            )

        )

        if (

            execution_result.execution_result.success

        ):

            return (

                AutonomousSalesResult(

                    success=True,

                    message="pipeline completed"

                )

            )

        return (

            AutonomousSalesResult(

                success=False,

                message="execution failed"

            )

        )