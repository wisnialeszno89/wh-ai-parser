from app.wh.runtime.vision.mail_recognizer import (
    MailRecognizer
)

from app.wh.runtime.vision.mail_to_customer_prediction_pipeline import (
    MailToCustomerPredictionPipeline
)

from app.wh.runtime.vision.mail_to_offer_pipeline import (
    MailToOfferPipeline
)


class MailSubsystem:

    def __init__(

        self,

        brain

    ):

        self.mail_recognizer = (

            MailRecognizer()

        )

        self.mail_to_customer_prediction_pipeline = (

            MailToCustomerPredictionPipeline(

                brain

            )

        )

        self.mail_to_offer_pipeline = (

            MailToOfferPipeline(

                brain

            )

        )