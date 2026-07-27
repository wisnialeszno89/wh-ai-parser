from app.runtime.execution.interactions.interaction_registry import (
    InteractionRegistry,
)


class InteractionRuntime:

    def __init__(self):

        self.registry = (
            InteractionRegistry()
        )

    def execute(
        self,
        context,
        plan,
    ):

        print()
        print("=" * 60)
        print("[INTERACTION RUNTIME]")
        print("=" * 60)

        for step in plan.steps:

            executor = self.registry.get(
                step.action,
            )

            if executor is None:

                raise RuntimeError(
                    f"No executor for {step.action}"
                )

            executor.execute(

                context,

                step,

            )