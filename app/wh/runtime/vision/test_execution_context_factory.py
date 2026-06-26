from app.wh.runtime.vision.execution_context_factory import (
    ExecutionContextFactory
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


def test_execution_context_factory():

    factory = (

        ExecutionContextFactory()

    )

    context = (

        factory.create(

            AdaptiveExecutionMode.NORMAL

        )

    )

    assert (

        context.retry_count

        ==

        3

    )

    context = (

        factory.create(

            AdaptiveExecutionMode.CAREFUL_MODE

        )

    )

    assert (

        context.retry_count

        ==

        5

    )

    assert (

        context.enable_logging

        is True

    )

    context = (

        factory.create(

            AdaptiveExecutionMode.SAFE_MODE

        )

    )

    assert (

        context.retry_count

        ==

        10

    )

    assert (

        context.enable_recovery

        is True

    )

    assert (

        context.enable_screenshots

        is True

    )