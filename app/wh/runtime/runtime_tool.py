from enum import Enum


class RuntimeTool(str, Enum):

    GLASS = "glass"

    COLOR = "color"

    HARDWARE = "hardware"

    PROFILE = "profile"

    DIMENSIONS = "dimensions"