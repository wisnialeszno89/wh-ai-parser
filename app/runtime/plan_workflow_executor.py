from app.wh.runtime.workflow_executor import (
    WorkflowExecutor
)


class PlanWorkflowExecutor:

    def __init__(

        self

    ):

        self.workflow = WorkflowExecutor()

    def execute(

        self,

        plan

    ):

        for window in plan.windows:

            self.workflow.execute(

            window

    )

        return True