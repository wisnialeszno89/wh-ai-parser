from enum import Enum


class ConstructionType(str, Enum):

    WINDOW = "WINDOW"

    DOOR = "DOOR"

    HST = "HST"

    PSK = "PSK"

    FACADE = "FACADE"

    UNKNOWN = "UNKNOWN"