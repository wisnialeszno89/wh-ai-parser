from app.wh.runtime.construction_pipeline import (
    ConstructionPipeline
)

from app.wh.runtime.actions.action_plan_executor import (
    ActionPlanExecutor
)


class RuntimeCoordinator:

    def __init__(

        self

    ):

        self.pipeline = (

            ConstructionPipeline()

        )

        self.executor = (

            ActionPlanExecutor()

        )

    def execute(

        self,

        construction

    ):

        plan = (

            self.pipeline.execute(

                construction

            )

        )

        return self.executor.execute(

            plan

        )