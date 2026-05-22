from app.wh.runtime.engine import WHRuntime

from app.wh.runtime.intent import (
    WindowIntent
)

from app.wh.runtime.canvas_target import (
    CanvasTarget
)

from app.wh.runtime.runtime_tool import (
    RuntimeTool
)

from app.wh.runtime.actions.models.select_tool_action import (
    SelectToolAction
)

from app.wh.runtime.actions.models.click_canvas_action import (
    ClickCanvasAction
)


def create_fix_workflow(

    intent: WindowIntent

):

    runtime = WHRuntime(
    intent
    )

    runtime.attach()

    runtime.focus()

    runtime.new_offer()

    runtime.add_window()

    runtime.set_dimensions(
        intent.width,
        intent.height
    )

    runtime.build_geometry(

    intent.geometry,

    intent
    )

    if intent.color:

        runtime.execute(
            SelectToolAction(
                RuntimeTool.COLOR
            )
        )

        runtime.execute(
            ClickCanvasAction(
                CanvasTarget.FRAME
            )
        )

        runtime.set_color(
            intent.color
        )

    runtime.save_offer()

    runtime.state.history.print()

    print(
        "[WORKFLOW] FIX created"
    )