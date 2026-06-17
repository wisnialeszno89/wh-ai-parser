from app.actions.executor.find_ui_object import (
    find_ui_object
)

from app.actions.models.action import (
    Action
)

from app.ui.risk.calculate_ui_risk import (
    calculate_ui_risk
)


SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

MAX_RISK = 0.7


def execute_action(

    action: Action,

    ui_graph
):

    if action.action_type == "select_tool":

        tool = find_ui_object(

            ui_graph,

            action.tool_name
        )

        if tool is None:

            print(

                f"[ERROR] tool not found: "
                f"{action.tool_name}"
            )

            return

        risk = calculate_ui_risk(

            tool,

            SCREEN_WIDTH,
            SCREEN_HEIGHT
        )

        print(
            f"[RISK] "
            f"{tool.label} "
            f"=> "
            f"{risk}"
        )

        if risk > MAX_RISK:

            print(
                "[BLOCKED] "
                "unsafe UI action"
            )

            return

        click_x = tool.x + tool.width // 2
        click_y = tool.y + tool.height // 2

        print(

            f"[EXECUTE] click "
            f"{action.tool_name} "
            f"at "
            f"({click_x}, {click_y})"
        )

    elif action.action_type == "draw_frame":

        print(
            "[EXECUTE] draw frame"
        )

    elif action.action_type == "insert_mullion":

        print(
            "[EXECUTE] insert mullion"
        )

    else:

        print(

            f"[EXECUTE] unknown: "
            f"{action.action_type}"
        )