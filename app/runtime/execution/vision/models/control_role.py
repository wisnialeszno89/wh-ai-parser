from enum import Enum


class ControlRole(str, Enum):
    """
    Semantic role of a GUI object.

    Roles describe the meaning of an object,
    independent of its visual representation.
    """

    UNKNOWN = "unknown"

    #
    # Application areas / sections
    #

    FRAME_SECTION = "frame_section"

    GLASS_SECTION = "glass_section"

    HARDWARE_SECTION = "hardware_section"

    ACCESSORIES_SECTION = "accessories_section"

    DIMENSIONS_SECTION = "dimensions_section"

    COLOR_SECTION = "color_section"

    #
    # WindowHub controls
    #

    FRAME = "frame"

    GLASS = "glass"

    HARDWARE = "hardware"

    ACCESSORIES = "accessories"

    WIDTH = "width"

    HEIGHT = "height"

    COLOR = "color"

    #
    # Generic actions
    #

    SAVE = "save"

    CANCEL = "cancel"

    CLOSE = "close"

    NEXT = "next"

    BACK = "back"

    SEARCH = "search"

    OK = "ok"