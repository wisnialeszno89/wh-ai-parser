from app.runtime.real_executor import (
    execute_real_action
)


def execute_real_plan(
    gui_actions
):

    commands = []

    for action in gui_actions:

        commands.extend(

            execute_real_action(
                action
            )

        )

    return commands