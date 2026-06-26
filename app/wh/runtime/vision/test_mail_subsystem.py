from app.wh.runtime.vision.mail_subsystem import (
    MailSubsystem
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)


def test_mail_subsystem():

    brain = (

        ProjectBrain()

    )

    subsystem = (

        MailSubsystem(

            brain

        )

    )

    assert (

        subsystem.mail_recognizer

        is not None

    )

    assert (

        subsystem.mail_to_customer_prediction_pipeline

        is not None

    )

    assert (

        subsystem.mail_to_offer_pipeline

        is not None

    )