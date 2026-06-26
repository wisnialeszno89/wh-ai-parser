from app.wh.runtime.vision.customer_prediction_pipeline_result import (
    CustomerPredictionPipelineResult
)


class CustomerPredictionPipeline:

    def __init__(

        self,

        brain

    ):

        self.brain = brain

    def execute(

        self,

        customer_name

    ):

        knowledge = (

            self.brain.customer_knowledge_engine.analyze(

                customer_name

            )

        )

        preference = (

            self.brain.customer_preference_engine.analyze(

                knowledge

            )

        )

        prediction = (

            self.brain.customer_prediction_engine.predict(

                preference

            )

        )

        return (

            CustomerPredictionPipelineResult(

                prediction=prediction

            )

        )