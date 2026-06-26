from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


def test_adaptive_execution_mode():

    assert (

        AdaptiveExecutionMode.NORMAL.value

        ==

        "normal"

    )

    assert (

        AdaptiveExecutionMode.SAFE_MODE.value

        ==

        "safe_mode"

    )

    assert (

        AdaptiveExecutionMode.CAREFUL_MODE.value

        ==

        "careful_mode"

    )

    assert (

        AdaptiveExecutionMode.RECOVERY_MODE.value

        ==

        "recovery_mode"

    )

    assert (

        AdaptiveExecutionMode.HUMAN_REVIEW_MODE.value

        ==

        "human_review_mode"

    )