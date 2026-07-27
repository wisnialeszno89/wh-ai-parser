from enum import Enum


class InteractionTarget(Enum):

    #
    # Frame properties
    #

    FRAME_WIDTH = "frame_width"

    FRAME_HEIGHT = "frame_height"

    FRAME_PROFILE = "frame_profile"

    FRAME_COLOR = "frame_color"

    #
    # Components
    #

    GLASS = "glass"

    HARDWARE = "hardware"

    EXTENSION = "extension"

    #
    # Construction
    #

    SASH = "sash"

    MULLION = "mullion"

    MOVABLE_MULLION = "movable_mullion"

    #
    # General
    #

    SAVE = "save"

    CONFIRM = "confirm"

    CANCEL = "cancel"