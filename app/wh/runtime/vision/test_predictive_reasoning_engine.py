from app.wh.runtime.vision.predictive_reasoning_engine import (
    PredictiveReasoningEngine
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)


def test_predictive_reasoning_engine():

    brain = (

        ProjectBrain()

    )

    brain.learning_memory.remember(

        "database_error",

        "enable_contacts"

    )

    brain.learning_memory.remember(

        "database_error",

        "enable_contacts"

    )

    engine = (

        PredictiveReasoningEngine()

    )

    warning = (

        engine.predict(

            GUIGoal(

                "enable_contacts"

            ),

            brain

        )

    )

    assert (

        warning

        is not None

    )

    assert (

        warning.reason

        ==

        "database_error"

    )

    assert (

        warning.confidence

        ==

        2

    )