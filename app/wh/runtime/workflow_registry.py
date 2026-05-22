from app.wh.runtime.workflows.create_fix import (
    create_fix_workflow
)


class WorkflowRegistry:

    def resolve(

        self,
        intent
    ):

        if intent.geometry == "FIX":

            return create_fix_workflow

        raise RuntimeError(
            f"No workflow for "
            f"{intent.geometry}"
        )