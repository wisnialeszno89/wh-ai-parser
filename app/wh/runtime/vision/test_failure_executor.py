from app.wh.runtime.vision.failure_executor import (
    FailureExecutor
)

from app.wh.runtime.vision.failure_reasoning_engine import (
    FailureReasoningEngine
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)


def test_failure_executor():

    brain = (

        ProjectBrain()

    )

    brain.gui_state.current_dialog = (

        "hardware"

    )

    engine = (

        FailureReasoningEngine()

    )

    decision = (

        engine.decide(

            "dialog_not_found",

            brain

        )

    )

    executor = (

        FailureExecutor()

    )

    assert (

        executor.execute(

            decision,

            brain

        )

        is True

    )

    assert (

        brain.gui_state.current_dialog

        is None

    )