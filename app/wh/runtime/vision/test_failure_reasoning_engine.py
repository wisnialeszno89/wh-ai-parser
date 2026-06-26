from app.wh.runtime.vision.failure_reasoning_engine import (
    FailureReasoningEngine
)

from app.wh.runtime.vision.project_brain import (
    ProjectBrain
)

from app.wh.runtime.vision.failure_action import (
    FailureAction
)


def test_failure_reasoning_engine():

    brain = (

        ProjectBrain()

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

    assert (

        decision.action

        ==

        FailureAction.RECOVER

    )

    assert (

        decision.reason

        ==

        "dialog_not_found"

    )