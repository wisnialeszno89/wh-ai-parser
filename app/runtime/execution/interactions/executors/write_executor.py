from app.runtime.execution.interactions.interaction_step import (
    InteractionStep,
)


class ClickExecutor:

    def execute(
        self,
        context,
        step: InteractionStep,
    ):

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