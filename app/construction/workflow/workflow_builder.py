from app.construction.workflow.workflow import (
    Workflow
)

from app.construction.workflow.workflow_step import (
    WorkflowStep
)


class WorkflowBuilder:

    def build(

        self,

        construction

    ):

        workflow = Workflow()

        workflow.steps.append(

            WorkflowStep(

                operation="FRAME"

            )

        )

        if construction.mullions:

            workflow.steps.append(

                WorkflowStep(

                    operation="MULLIONS"

                )

            )

        workflow.steps.append(

            WorkflowStep(

                operation="SASHES"

            )

        )

        workflow.steps.append(

            WorkflowStep(

                operation="HARDWARE"

            )

        )

        workflow.steps.append(

            WorkflowStep(

                operation="GLASS"

            )

        )

        return workflow