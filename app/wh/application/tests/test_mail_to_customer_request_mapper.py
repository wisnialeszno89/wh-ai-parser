from app.wh.application.mail.mail_to_customer_request_mapper import (
    MailToCustomerRequestMapper
)

from app.wh.runtime.vision.mail_metadata import (
    MailMetadata
)

from app.wh.runtime.vision.mail_recognition_result import (
    MailRecognitionResult
)


def test_mail_to_customer_request_mapper():

    mapper = MailToCustomerRequestMapper()

    recognition = MailRecognitionResult(

        metadata=MailMetadata(

            sender_email="info@muller.de",

            sender_name="Hans Müller",

            company="Muller GmbH",

            language="de"

        ),

        subject="Request",

        body="8 windows"

    )

    request = mapper.map(

        recognition

    )

    assert request.customer.name == "Muller GmbH"

    assert request.customer.email == "info@muller.de"

    assert request.language == "de"

    assert len(request.products) == 1

    assert request.products[0].category == "window"