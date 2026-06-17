from enum import Enum


class OpeningType(str, Enum):

    FIX = "FIX"

    RU = "RU"

    R = "R"

    U = "U"

    DOOR = "DOOR"

    HST = "HST"

    PSK = "PSK"

    UNKNOWN = "UNKNOWN"