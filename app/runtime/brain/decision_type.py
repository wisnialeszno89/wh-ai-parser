from enum import Enum


class DecisionType(str, Enum):

    CONTINUE = "continue"

    RETRY = "retry"

    SKIP = "skip"

    STOP = "stop"