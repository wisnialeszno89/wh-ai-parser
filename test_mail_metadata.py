from app.wh.runtime.vision.mail_metadata import (
    MailMetadata
)


def test_mail_metadata():

    metadata = (

        MailMetadata(

            sender_email="info@test.de",

            sender_name="Max Mustermann",

            company="Test GmbH",

            language="de",

            priority="high",

            request_type="quotation"

        )

    )

    assert metadata.sender_email == "info@test.de"

    assert metadata.company == "Test GmbH"

    assert metadata.language == "de"

    assert metadata.priority == "high"

    assert metadata.request_type == "quotation"