from app.wh.runtime.vision.vision_decision import (
    VisionDecision
)


def test_vision_decision():

    decision = (

        VisionDecision(

            execute=True,

            reason="not_completed"

        )

    )

    assert (

        decision.execute

        is True

    )

    assert (

        decision.reason

        ==

        "not_completed"

    )