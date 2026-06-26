from app.wh.runtime.vision.mail_parser import (
    MailParser
)


def test_mail_parser():

    parser = (

        MailParser()

    )

    metadata = (

        parser.parse(

            "Bitte Angebot",

            """

            Guten Tag,

            bitte senden Sie ein Angebot.

            info@test.de

            """

        )

    )

    assert (

        metadata.sender_email

        ==

        "info@test.de"

    )

    assert (

        metadata.language

        ==

        "de"

    )

    assert (

        metadata.request_type

        ==

        "quotation"

    )

    assert (

        metadata.priority

        ==

        "normal"

    )