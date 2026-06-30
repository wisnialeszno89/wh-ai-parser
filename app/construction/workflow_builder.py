from app.construction.construction_plan import (
    ConstructionPlan
)

from app.construction.construction_step import (
    ConstructionStep
)


class WorkflowBuilder:

    def build(
        self,
        workflow: dict
    ) -> ConstructionPlan:

        plan = ConstructionPlan()

        for step in workflow["steps"]:

            plan.steps.append(

                ConstructionStep(

                    action=step["action"]
                )
            )

        return plan