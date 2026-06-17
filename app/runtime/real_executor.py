from app.runtime.screen_model import (
    SCREEN
)

from app.runtime.locator import (
    locate_element
)

from app.runtime.fake_pyautogui import (
    click,
    write
)


def execute_real_action(
    action
):

    commands = []

    element = SCREEN[
        action.control
    ]

    x, y = locate_element(
        element
    )

    #
    # select
    #

    if action.action == "select":

        commands.append(

            click(

                x,

                y

            )

        )

        commands.append(

            write(

                action.value

            )

        )

    #
    # click
    #

    elif action.action == "click":

        commands.append(

            click(

                x,

                y

            )

        )

    #
    # type
    #

    elif action.action == "type":

        commands.append(

            write(

                action.value

            )

        )

    return commands