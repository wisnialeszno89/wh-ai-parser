from app.wh.runtime.vision.mail_to_offer_pipeline import (
    MailToOfferPipeline
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)


def test_mail_to_offer_pipeline():

    brain = (

        ProjectBrain()

    )

    pipeline = (

        MailToOfferPipeline(

            brain

        )

    )

    result = (

        pipeline.execute(

            "Please prepare quotation"

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

    assert (

        result.offer.color

        ==

        "Anthracite"

    )

    assert (

        result.offer.addon

        ==

        "RC2"

    )