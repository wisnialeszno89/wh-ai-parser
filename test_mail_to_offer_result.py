from app.wh.runtime.vision.mail_to_offer_result import (
    MailToOfferResult
)


def test_mail_to_offer_result():

    result = (

        MailToOfferResult(

            success=True,

            customer_name="Muller GmbH",

            offer_number="2026-0001"

        )

    )

    assert (

        result.success

        is True

    )

    assert (

        result.customer_name

        ==

        "Muller GmbH"

    )

    assert (

        result.offer_number

        ==

        "2026-0001"

    )