from enum import Enum


class EnvironmentPreparationType(str, Enum):
    """
    Describes what should happen to prepare the environment.
    """

    READY = "ready"

    PREPARE = "prepare"

    USER_ACTION_REQUIRED = "user_action_required"

    MANUAL_REVIEW = "manual_review"

    STOP = "stop"
