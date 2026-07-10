from enum import Enum


class ControlState(str, Enum):
    """
    Current visual state of a GUI control.
    """

    UNKNOWN = "unknown"

    VISIBLE = "visible"

    HIDDEN = "hidden"

    ENABLED = "enabled"

    DISABLED = "disabled"

    ACTIVE = "active"

    INACTIVE = "inactive"

    SELECTED = "selected"

    UNSELECTED = "unselected"

    FOCUSED = "focused"

    PRESSED = "pressed"