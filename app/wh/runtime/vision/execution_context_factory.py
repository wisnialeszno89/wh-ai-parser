from app.wh.runtime.vision.execution_context import (
    ExecutionContext
)

from app.wh.runtime.vision.adaptive_execution_mode import (
    AdaptiveExecutionMode
)


class ExecutionContextFactory:

    def create(

        self,

        mode

    ):

        if (

            mode

            ==

            AdaptiveExecutionMode.CAREFUL_MODE

        ):

            return (

                ExecutionContext(

                    mode=mode,

                    retry_count=5,

                    enable_logging=True

                )

            )

        if (

            mode

            ==

            AdaptiveExecutionMode.SAFE_MODE

        ):

            return (

                ExecutionContext(

                    mode=mode,

                    retry_count=10,

                    enable_logging=True,

                    enable_recovery=True,

                    enable_screenshots=True

                )

            )

        if (

            mode

            ==

            AdaptiveExecutionMode.HUMAN_REVIEW_MODE

        ):

            return (

                ExecutionContext(

                    mode=mode,

                    retry_count=0

                )

            )

        return (

            ExecutionContext(

                mode=mode

            )

        )