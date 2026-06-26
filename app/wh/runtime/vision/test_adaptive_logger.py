from app.wh.runtime.vision.adaptive_logger import (
    AdaptiveLogger
)

from app.wh.runtime.vision.execution_context import (
    ExecutionContext
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


def test_adaptive_logger():

    logger = (

        AdaptiveLogger()

    )

    context = (

        ExecutionContext(

            mode=AdaptiveExecutionMode.CAREFUL_MODE,

            enable_logging=True

        )

    )

    logger.log(

        "test",

        context

    )

    assert (

        True

    )