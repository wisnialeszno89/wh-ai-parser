from app.runtime.execution.contracts.interaction_executor import (
    InteractionExecutor,
)

from app.runtime.execution.execution_result import (
    ExecutionResult,
)

from app.runtime.execution.interactions.interaction_step import (
    InteractionStep,
)

from app.runtime.execution.mouse_controller import (
    MouseController,
)


class ClickExecutor(InteractionExecutor):

    def __init__(
        self,
        mouse: MouseController | None = None,
    ):
        self.mouse = mouse or MouseController()

    def execute(
        self,
        context,
        step: InteractionStep,
    ) -> ExecutionResult:

        print()
        print(f"[CLICK] {step.target}")

        visual_target = step.visual_target

        if visual_target is None:
            return ExecutionResult.fail(
                "CLICK requires a visual_target."
            )

        bounds = getattr(
            visual_target,
            "bounds",
            None,
        )

        if bounds is None:
            return ExecutionResult.fail(
                "CLICK visual_target has no bounds."
            )

        window = getattr(
            context,
            "window",
            None,
        )

        if window is None:
            return ExecutionResult.fail(
                "CLICK requires window origin."
            )

        local_x, local_y = bounds.center

        screen_x = int(
            window.left + local_x
        )

        screen_y = int(
            window.top + local_y
        )

        print(
            f"[CLICK] local=({local_x}, {local_y}) "
            f"origin=({window.left}, {window.top}) "
            f"screen=({screen_x}, {screen_y})"
        )

        self.mouse.click(
            screen_x,
            screen_y,
        )

        return ExecutionResult.ok(
            message=(
                f"Clicked visual target "
                f"local=({local_x}, {local_y}) "
                f"screen=({screen_x}, {screen_y})."
            )
        )
