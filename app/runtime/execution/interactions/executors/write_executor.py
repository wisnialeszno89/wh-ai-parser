from app.runtime.execution.contracts.interaction_executor import (
    InteractionExecutor,
)

from app.runtime.execution.execution_result import (
    ExecutionResult,
)

from app.runtime.execution.interactions.interaction_step import (
    InteractionStep,
)


class WriteExecutor(InteractionExecutor):

    def execute(
        self,
        context,
        step: InteractionStep,
    ) -> ExecutionResult:

        print()
        print(f"[WRITE] {step.value}")

        context.keyboard.write(
            step.value,
        )

        return ExecutionResult.ok()