from app.wh.runtime.vision.mail_to_offer_pipeline_result import (
    MailToOfferPipelineResult
)


class MailToOfferPipeline:

    def __init__(

        self,

        brain

    ):

        self.brain = brain

    def execute(

        self,

        mail_text

    ):

        prediction_result = (

            self.brain.mail_to_customer_prediction_pipeline.execute(

                mail_text

            )

        )

        offer = (

            self.brain.offer_builder.build(

                prediction_result.prediction

            )

        )

        return (

            MailToOfferPipelineResult(

                offer=offer

            )

        )