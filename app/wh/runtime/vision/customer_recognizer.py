from app.wh.runtime.vision.customer_recognition_result import (
    CustomerRecognitionResult
)


class CustomerRecognizer:

    def recognize(

        self,

        mail_result

    ):

        return (

            CustomerRecognitionResult(

                customer_name=(

                    mail_result.customer_name

                ),

                recognized=True

            )

        )