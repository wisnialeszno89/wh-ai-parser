from app.wh.runtime.vision.mail_to_customer_prediction_pipeline import (
    MailToCustomerPredictionPipeline
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)


def test_mail_to_customer_prediction_pipeline():

    brain = (

        ProjectBrain()

    )

    pipeline = (

        MailToCustomerPredictionPipeline(

            brain

        )

    )

    result = (

        pipeline.execute(

            "Please prepare quotation"

        )

    )

    assert (

        result.prediction.customer_name

        ==

        "Muller GmbH"

    )

    assert (

        result.prediction.profile

        ==

        "Softline82"

    )

    assert (

        result.prediction.color

        ==

        "Anthracite"

    )

    assert (

        result.prediction.addon

        ==

        "RC2"

    )