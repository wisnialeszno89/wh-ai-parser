from app.wh.runtime.vision.mail_to_customer_prediction_result import (
    MailToCustomerPredictionResult
)


class MailToCustomerPredictionPipeline:

    def __init__(

        self,

        brain

    ):

        self.brain = brain

    def execute(

        self,

        mail_text

    ):

        mail_result = (

            self.brain.mail_recognizer.recognize(

                mail_text

            )

        )

        customer_result = (

            self.brain.customer_recognizer.recognize(

                mail_result

            )

        )

        prediction_result = (

            self.brain.customer_prediction_pipeline.execute(

                customer_result.customer_name

            )

        )

        return (

            MailToCustomerPredictionResult(

                prediction=(

                    prediction_result.prediction

                )

            )

        )