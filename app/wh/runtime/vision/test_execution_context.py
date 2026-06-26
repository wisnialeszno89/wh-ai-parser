from app.wh.runtime.vision.execution_context import (
    ExecutionContext
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


def test_execution_context():

    context = (

        ExecutionContext(

            mode=AdaptiveExecutionMode.NORMAL

        )

    )

    assert (

        context.retry_count

        ==

        3

    )

    assert (

        context.enable_logging

        is False

    )

    assert (

        context.enable_recovery

        is False

    )

    assert (

        context.enable_screenshots

        is False

    )