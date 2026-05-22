from app.wh.runtime.constructions.executors.base_executor import (
    BaseExecutor
)

from app.wh.runtime.actions.action_pipeline import (
    ActionPipeline
)

from app.wh.runtime.actions.click_action import (
    ClickAction
)

from app.wh.runtime.actions.select_tool_action_runtime import (
    SelectToolActionRuntime
)


class RuExecutor(

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
            "[EXECUTOR] RU"
        )

        pipeline = (
            ActionPipeline()
        )

        pipeline.add(

            SelectToolActionRuntime(
                "glass"
            )
        )

        pipeline.add(

            ClickAction(
                x,
                y
            )
        )

        pipeline.run(
            runtime
        )

        pipeline.export(
            "runtime_data/ru_pipeline.json"
        )

        print(
            "[RU] open sash menu"
        )

        print(
            "[RU] select opening type"
        )