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

        print(
            f"Steps: {len(plan.steps)}"
        )

        for index, step in enumerate(
            plan.steps,
            start=1,
        ):

            print()

            print(
                f"[STEP {index}/{len(plan.steps)}]"
            )

            print(
                f"Action : {step.action}"
            )

            print(
                f"Target : {step.target}"
            )

            print(
                f"Value  : {step.value}"
            )

            executor = self.registry.get(
                step.action,
            )

            if executor is None:

                raise RuntimeError(
                    f"No executor for {step.action}"
                )

            print(
                f"Executor : {executor.__class__.__name__}"
            )

            executor.execute(

                context,

                step,

            )

        print()

        print(
            "[INTERACTION RUNTIME FINISHED]"
        )