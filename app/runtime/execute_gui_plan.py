from app.runtime.executor_runtime import (
    execute_gui_action
)


def execute_gui_plan(
    gui_actions
):

    commands = []

    for action in gui_actions:

        commands.extend(

            execute_gui_action(
                action
            )

        )

    return commands