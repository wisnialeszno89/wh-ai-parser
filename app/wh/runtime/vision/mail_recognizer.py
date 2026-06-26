from app.wh.runtime.vision.mail_recognition_result import (
    MailRecognitionResult
)


class MailRecognizer:

    def recognize(

        self,

        mail_text

    ):

        return (

            MailRecognitionResult(

                customer_name="Muller GmbH",

                subject="New request",

                body=mail_text

            )

        )