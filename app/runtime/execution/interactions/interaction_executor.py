from app.runtime.execution.keyboard.keyboard_controller import (
    KeyboardController,
)

from app.runtime.execution.interactions.executors.click_executor import (
    ClickExecutor,
)

from app.runtime.execution.interactions.executors.verify_executor import (
    VerifyExecutor,
)

from app.runtime.execution.interactions.interaction_action import (
    InteractionAction,
)

from app.runtime.execution.interactions.interaction_plan import (
    InteractionPlan,
)


class InteractionExecutor:

    def __init__(self):

        self.keyboard = KeyboardController()

        self.click = ClickExecutor()

        self.verify = VerifyExecutor()

    def execute(
        self,
        plan: InteractionPlan,
    ):

        if not plan.steps:

            return

        print()
        print("=" * 60)
        print("[INTERACTIONS]")
        print("=" * 60)

        for step in plan.steps:

            print(
                f"[{step.action.name}] "
                f"{step.target or ''} "
                f"{step.value or ''}"
            )

            if step.action == InteractionAction.WRITE:

                self.keyboard.write(
                    step.value,
                )

            elif step.action == InteractionAction.CLICK:

                self.click.execute(
                    None,
                    step,
                )

            elif step.action == InteractionAction.VERIFY:

                self.verify.execute(
                    None,
                    step,
                )

        print("=" * 60)