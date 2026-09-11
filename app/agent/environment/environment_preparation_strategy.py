from enum import Enum


class EnvironmentPreparationStrategy(
    str,
    Enum,
):
    """
    Describes the semantic strategy used to prepare
    the environment for agent execution.

    A strategy describes HOW the environment should
    conceptually be prepared without depending on a
    specific operating system or automation technology.
    """

    NONE = "none"

    ACTIVATE_APPLICATION = (
        "activate_application"
    )

    FOCUS_WINDOW = "focus_window"

    LAUNCH_APPLICATION = (
        "launch_application"
    )

    REQUEST_USER_ACTION = (
        "request_user_action"
    )
