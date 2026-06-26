from app.wh.runtime.vision.customer_recognizer import (
    CustomerRecognizer
)

from app.wh.runtime.vision.mail_recognition_result import (
    MailRecognitionResult
)


def test_customer_recognizer():

    recognizer = (

        CustomerRecognizer()

    )

    mail = (

        MailRecognitionResult(

            customer_name="Muller GmbH",

            subject="New request",

            body="Please prepare quotation"

        )

    )

    result = (

        recognizer.recognize(

            mail

        )

    )

    assert (

        result.customer_name

        ==

        "Muller GmbH"

    )

    assert (

        result.recognized

        is True

    )