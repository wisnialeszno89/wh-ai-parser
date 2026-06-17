# app/knowledge/types/opening_types.py

from enum import Enum


class OpeningType(str, Enum):

    FIX = "fixed"

    RU = "tilt_turn"

    R = "turn"

    U = "tilt"

    DOOR = "door"

    HST_LEFT = "hst_left"
    HST_RIGHT = "hst_right"

    PSK_LEFT = "psk_left"
    PSK_RIGHT = "psk_right"