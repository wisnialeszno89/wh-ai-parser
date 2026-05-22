from app.wh.runtime.constructions.executors.base_executor import (
    BaseExecutor
)


class FixExecutor(

    BaseExecutor
):

    def execute(

        self,
        runtime,
        x,
        y,
        segment
    ):

        print(
            "[EXECUTOR] FIX"
        )

        runtime.click_position(
            x,
            y
        )