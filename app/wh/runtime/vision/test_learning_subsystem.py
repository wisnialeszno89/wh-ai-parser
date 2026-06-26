from app.wh.runtime.vision.learning_subsystem import (
    LearningSubsystem
)


def test_learning_subsystem():

    subsystem = (

        LearningSubsystem()

    )

    assert (

        subsystem.learning_from_failures_engine

        is not None

    )