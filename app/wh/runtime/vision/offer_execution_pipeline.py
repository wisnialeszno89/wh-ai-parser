from app.wh.runtime.vision.offer_execution_pipeline_result import (
    OfferExecutionPipelineResult
)


class OfferExecutionPipeline:

    def __init__(

        self,

        brain

    ):

        self.brain = brain

    def execute(

        self,

        offer

    ):

        plan = (

            self.brain.offer_execution_planner.create_plan(

                offer

            )

        )

        execution_result = (

            self.brain.intelligent_vision_executor.execute(

                plan

            )

        )

        return (

            OfferExecutionPipelineResult(

                execution_result=execution_result

            )

        )