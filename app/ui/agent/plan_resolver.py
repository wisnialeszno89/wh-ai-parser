from app.ui.agent.gui_function_registry import (
    get_gui_function
)


def resolve_plan(
    actions
):

    resolved = []

    for action in actions:

        gui_function = (

            get_gui_function(
                action.action
            )
        )

        resolved.append({

            "action":
                action.action,

            "params":
                action.params,

            "gui_function":
                gui_function
        })

    return resolved