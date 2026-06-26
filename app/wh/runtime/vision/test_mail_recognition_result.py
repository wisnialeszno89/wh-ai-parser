from app.wh.runtime.vision.mail_recognition_result import (
    MailRecognitionResult
)

from app.wh.runtime.vision.mail_metadata import (
    MailMetadata
)


def test_mail_recognition_result():

    result = (

        MailRecognitionResult(

            metadata=(

                MailMetadata(

                    sender_email="info@test.de",

                    company="Test GmbH",

                    language="de"

                )

            ),

            subject="Neue Anfrage",

            body="Please prepare quotation"

        )

    )

    assert result.metadata.company == "Test GmbH"

    assert result.metadata.language == "de"

    assert result.subject == "Neue Anfrage"