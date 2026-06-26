from app.wh.runtime.vision.learning_engine import (
    LearningEngine
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.failure_record import (
    FailureRecord
)


def test_learning_engine():

    brain = (

        ProjectBrain()

    )

    brain.failure_history.remember(

        FailureRecord(

            goal="enable_contacts",

            reason="database_error"

        )

    )

    brain.failure_history.remember(

        FailureRecord(

            goal="enable_contacts",

            reason="database_error"

        )

    )

    engine = (

        LearningEngine()

    )

    engine.learn(

        brain

    )

    assert (

        brain.learning_memory.count()

        ==

        1

    )

    assert (

        brain.learning_memory.records[0].occurrences

        ==

        2

    )