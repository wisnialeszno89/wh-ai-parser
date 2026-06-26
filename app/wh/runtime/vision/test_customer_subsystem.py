from app.wh.runtime.vision.customer_subsystem import (
    CustomerSubsystem
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)


def test_customer_subsystem():

    brain = (

        ProjectBrain()

    )

    subsystem = (

        CustomerSubsystem(

            brain

        )

    )

    assert (

        subsystem.customer_recognizer

        is not None

    )

    assert (

        subsystem.customer_knowledge_engine

        is not None

    )

    assert (

        subsystem.customer_preference_engine

        is not None

    )

    assert (

        subsystem.customer_prediction_engine

        is not None

    )

    assert (

        subsystem.customer_prediction_pipeline

        is not None

    )