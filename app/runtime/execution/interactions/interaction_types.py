from enum import Enum


class InteractionType(str, Enum):

    TAB = "TAB"

    ENTER = "ENTER"

    WRITE = "WRITE"

    HOTKEY = "HOTKEY"

    CLICK = "CLICK"