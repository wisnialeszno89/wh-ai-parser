from app.wh.runtime.vision.mail_recognizer import (
    MailRecognizer
)


def test_mail_recognizer():

    recognizer = (

        MailRecognizer()

    )

    result = (

        recognizer.recognize(

            "Please prepare quotation"

        )

    )

    assert (

        result.customer_name

        ==

        "Muller GmbH"

    )

    assert (

        result.body

        ==

        "Please prepare quotation"

    )