from enum import Enum


class InteractionAction(Enum):

    CLICK = "click"

    DOUBLE_CLICK = "double_click"

    RIGHT_CLICK = "right_click"

    WRITE = "write"

    SELECT = "select"

    WAIT = "wait"

    VERIFY = "verify"