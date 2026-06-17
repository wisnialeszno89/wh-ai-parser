from app.runtime.screen_model import (
    SCREEN
)


def execute_gui_action(
    action
):

    commands = []

    element = SCREEN[
        action.control
    ]

    #
    # select
    #

    if (

        action.action

        ==

        "select"

    ):

        commands.append(

            f"CLICK {element.x} {element.y}"

        )

        commands.append(

            f"WRITE {action.value}"

        )

    #
    # click
    #

    elif (

        action.action

        ==

        "click"

    ):

        commands.append(

            f"CLICK {element.x} {element.y}"

        )

    #
    # type
    #

    elif (

        action.action

        ==

        "type"

    ):

        commands.append(

            f"WRITE {action.value}"

        )

    return commands