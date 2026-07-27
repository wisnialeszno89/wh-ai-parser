from enum import Enum


class GuiTarget(Enum):

    #
    # Frame
    #

    FRAME_WIDTH = "frame_width"

    FRAME_HEIGHT = "frame_height"

    FRAME_PROFILE = "frame_profile"

    FRAME_COLOR = "frame_color"

    #
    # Buttons
    #

    ADD_SASH = "add_sash"

    SAVE = "save"

    CANCEL = "cancel"

    OK = "ok"

    #
    # Hardware
    #

    HARDWARE = "hardware"

    GLASS = "glass"