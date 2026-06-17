from app.runtime.models.runtime_command import (
    RuntimeCommand
)

from app.actions.executor.find_ui_object import (
    find_ui_object
)


def serialize_plan(

    plan,

    ui_graph
):

    commands = []

    for action in plan.actions:

        if action.action_type == "select_tool":

            tool = find_ui_object(

                ui_graph,

                action.tool_name
            )

            if tool is None:

                continue

            click_x = tool.x + tool.width // 2
            click_y = tool.y + tool.height // 2

            commands.append(

                RuntimeCommand(

                    command_type="click",

                    x=click_x,
                    y=click_y
                )
            )

        elif action.action_type == "draw_frame":

            commands.append(

                RuntimeCommand(

                    command_type="mouse_drag",

                    x=300,
                    y=300
                )
            )

    return commands