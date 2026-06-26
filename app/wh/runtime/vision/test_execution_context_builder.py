from app.wh.runtime.vision.execution_context_builder import (
    ExecutionContextBuilder
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.gui_goal import (
    GUIGoal
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


def test_execution_context_builder():

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

    builder = (

        ExecutionContextBuilder()

    )

    context = (

        builder.build(

            GUIGoal(

                "enable_contacts"

            ),

            brain

        )

    )

    assert (

        context.mode

        ==

        AdaptiveExecutionMode.CAREFUL_MODE

    )

    assert (

        context.enable_logging

        is True

    )

    assert (

        context.retry_count

        ==

        5

    )