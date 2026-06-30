from enum import Enum


class OpeningType(Enum):

    FIX = "FIX"

    TURN = "TURN"

    TILT = "TILT"

    TILT_TURN = "TILT_TURN"

    PSK = "PSK"

    HST = "HST"

    DOOR = "DOOR"