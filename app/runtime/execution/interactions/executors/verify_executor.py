from app.runtime.execution.contracts.interaction_executor import (
    InteractionExecutor,
)

from app.runtime.execution.execution_result import (
    ExecutionResult,
)

from app.runtime.execution.interactions.interaction_step import (
    InteractionStep,
)


class VerifyExecutor(InteractionExecutor):

    def execute(
        self,
        context,
        step: InteractionStep,
    ) -> ExecutionResult:

        print()
        print(f"[VERIFY] {step.target}")

        #
        # TODO:
        # Vision verification
        #

        return ExecutionResult.ok()