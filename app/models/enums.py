from enum import Enum


class ConstructionCategory(
    str,
    Enum
):

    WINDOW = "window"

    DOOR = "door"

    HST = "hst"

    PSK = "psk"

    GARAGE_GATE = "garage_gate"

    ROLLER_SHUTTER = "roller_shutter"


class OpeningType(
    str,
    Enum
):

    FIXED = "fixed"

    TILT = "tilt"

    TURN = "turn"

    TILT_TURN = "tilt_turn"

    SLIDING = "sliding"

    HST = "hst"

    PSK = "psk"


class SegmentKind(
    str,
    Enum
):

    LEFT = "left"

    RIGHT = "right"

    FIX = "fix"

    MIDDLE = "middle"

    FULL = "full"