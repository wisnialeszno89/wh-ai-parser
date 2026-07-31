from enum import Enum


class FailureType(str, Enum):

    NONE = "none"

    UNKNOWN = "unknown"

    TRANSIENT = "transient"

    PERMANENT = "permanent"