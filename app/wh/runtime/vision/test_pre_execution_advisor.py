from app.wh.runtime.vision.pre_execution_advisor import (
    PreExecutionAdvisor
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)

from app.wh.runtime.vision.prediction_strategy import (
    PredictionStrategy
)


def test_pre_execution_advisor():

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

    brain.learning_memory.remember(

        "database_error",

        "enable_contacts"

    )

    brain.learning_memory.remember(

        "database_error",

        "enable_contacts"

    )

    advisor = (

        PreExecutionAdvisor()

    )

    advice = (

        advisor.advise(

            GUIGoal(

                "enable_contacts"

            ),

            brain

        )

    )

    assert (

        advice.strategy

        ==

        PredictionStrategy.EXTRA_LOGGING

    )

    assert (

        advice.risk_reason

        ==

        "database_error"

    )

    assert (

        advice.confidence

        ==

        4

    )