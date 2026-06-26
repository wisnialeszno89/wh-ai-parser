from app.wh.runtime.vision.mail_to_offer_pipeline_result import (
    MailToOfferPipelineResult
)

from app.wh.runtime.vision.offer_schema import (
    OfferSchema
)


def test_mail_to_offer_pipeline_result():

    result = (

        MailToOfferPipelineResult(

            offer=(

                OfferSchema(

                    customer_name="Muller GmbH",

                    profile="Softline82",

                    color="Anthracite",

                    addon="RC2"

                )

            )

        )

    )

    assert (

        result.offer.customer_name

        ==

        "Muller GmbH"

    )

    assert (

        result.offer.profile

        ==

        "Softline82"

    )