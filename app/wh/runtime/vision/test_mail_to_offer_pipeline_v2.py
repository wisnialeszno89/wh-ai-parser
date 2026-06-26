from app.wh.runtime.vision.mail_to_offer_pipeline_v2 import (
    MailToOfferPipelineV2
)


def test_mail_to_offer_pipeline_v2():

    pipeline = (

        MailToOfferPipelineV2()

    )

    offer = (

        pipeline.execute(

            subject="Quotation",

            body="""

            Please prepare quotation.

            8 windows

            Anthracite outside

            White inside

            Triple glazing

            RC2

            """

        )

    )

    assert len(

        offer.products

    ) == 1

    product = offer.products[0]

    assert product.quantity == 8

    assert product.security == "RC2"

    assert product.profile == "VEKA Softline 82 MD"