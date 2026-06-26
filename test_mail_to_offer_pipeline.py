from app.wh.runtime.vision.mail_to_offer_pipeline import (
    MailToOfferPipeline
)


def test_mail_to_offer_pipeline():

    pipeline = (

        MailToOfferPipeline()

    )

    result = (

        pipeline.execute(

            "dummy mail"

        )

    )

    assert (

        result.success

        is True

    )