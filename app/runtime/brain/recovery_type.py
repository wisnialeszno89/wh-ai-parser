from enum import Enum


class RecoveryType(str, Enum):

    NONE = "none"

    REFRESH_WORLD = "refresh_world"

    REFRESH_SCREEN = "refresh_screen"

    FIND_WINDOW = "find_window"