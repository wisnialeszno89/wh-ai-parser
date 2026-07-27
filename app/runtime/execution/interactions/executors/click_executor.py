from app.runtime.execution.execution_result import ExecutionResult

from app.runtime.execution.interactions.interaction_step import (
    InteractionStep,
)


class ClickExecutor:

    def execute(
        self,
        context,
        step: InteractionStep,
    ) -> ExecutionResult:

        print()

        print(
            f"[CLICK] {step.target}"
        )

        #
        # TODO
        #
        # TargetLocator
        # Vision
        # MouseController
        #

        return ExecutionResult.ok()