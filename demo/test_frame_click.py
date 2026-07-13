from app.runtime.execution.context.execution_context import (
    ExecutionContext,
)

from app.runtime.execution.execution_runtime import (
    ExecutionRuntime,
)

from app.runtime.mission.gui_plan import GuiPlan
from app.runtime.mission.gui_action import GuiAction

from app.gui.enums.gui_tool import GuiTool


def main():

    print("=" * 60)
    print("FRAME CLICK TEST")
    print("=" * 60)

    plan = GuiPlan(
        actions=[
            GuiAction(
                tool=GuiTool.FRAME,
            )
        ]
    )

    runtime = ExecutionRuntime(
        ExecutionContext(
            mouse_enabled=True,
        )
    )

    runtime.execute(plan)


if __name__ == "__main__":
    main()